'''
Common functions and utilities

(c) 2009 - 2015 Greymind Inc.
    Balakrishnan (Balki) Ranganathan (balki_live_com)
    All Rights Reserved.
'''

import os
import io
import sys
import re
import math
import shutil
import fnmatch
import datetime
import maya.cmds as Cmds
import maya.mel as Mel
import xml.dom.minidom as Dom
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

global InfiniteLoopCounter

def StartInfinity():
    global InfiniteLoopCounter
    InfiniteLoopCounter = 0
    
def CheckInfinity(infinity=1000):
    global InfiniteLoopCounter
    InfiniteLoopCounter = InfiniteLoopCounter + 1
    
    if InfiniteLoopCounter >= infinity:
        print 'Loop overboard!'
        return True
    
    return False

def Nop():
    return

def IsNoneOrEmpty(string):
    return string is None or len(string) == 0
    
def IsZero(vector):
    return vector[0] == 0 and vector[1] == 0 and vector[2] == 0
    
def IsOne(vector):
    return vector[0] == 1 and vector[1] == 1 and vector[2] == 1

class XmlWriter:
    fileIndentLevel = 0
    defFile = ""
    
    def __init__(self, defFile):
        self.defFile = defFile

    def PushIndentLevel(self):
        self.fileIndentLevel += 1
        
    def PopIndentLevel(self):
        self.fileIndentLevel -= 1
        
    def WriteSpaces(self):
        for i in range(self.fileIndentLevel):
            self.defFile.write("    ")

    def WriteAttribute(self, key, value):
        self.defFile.write(" %s=\"%s\" " % (key, value))

    def WriteStartElement(self, elementName):
        self.WriteSpaces()
        self.defFile.write("<%s>\n" % elementName)
        self.PushIndentLevel()
        
    def WriteEndElement(self, elementName):
        self.PopIndentLevel()
        self.WriteSpaces()
        self.defFile.write("</%s>\n" % elementName)

    def WriteElementStart(self, elementName):
        self.WriteSpaces()
        self.defFile.write("<%s" % elementName)
        
    def WriteElementEnd(self, endElement = False):
        if endElement == True:
            self.defFile.write("/>\n")
        else:
            self.defFile.write(">\n")
            self.PushIndentLevel()

    def WriteXYZElement(self, elementName, xyz):
        self.WriteElementStart(elementName)
        self.WriteAttribute("X", NaNToNumber(xyz[0], 0))
        self.WriteAttribute("Y", NaNToNumber(xyz[1], 0))
        self.WriteAttribute("Z", NaNToNumber(xyz[2], 0))
        self.WriteElementEnd(True)

    def WriteXYZWElement(self, elementName, xyzw):
        self.WriteElementStart(elementName)
        self.WriteAttribute("X", NaNToNumber(xyzw[0], 0))
        self.WriteAttribute("Y", NaNToNumber(xyzw[1], 0))
        self.WriteAttribute("Z", NaNToNumber(xyzw[2], 0))
        self.WriteAttribute("W", NaNToNumber(xyzw[3], 1))
        self.WriteElementEnd(True)
        
    def WriteMatrixElement(self, elementName, matrix):
        self.WriteElementStart(elementName)
        
        for row in range(4):
            for column in range(4):
                self.WriteAttribute("M%d%d" % (row, column), matrix(row, column))
        
        self.WriteElementEnd(True)
        
    def WriteValueElement(self, elementName, value):
        self.WriteElementStart(elementName)
        self.WriteAttribute("Value", value)
        self.WriteElementEnd(True)

def PrintXYZ(xyz):
    print "X", str(xyz[0]),
    print "Y", str(xyz[1]),
    print "Z", str(xyz[2])

def PrintXYZW(xyzw):
    print "X", str(xyzw[0]),
    print "Y", str(xyzw[1]),
    print "Z", str(xyzw[2]),
    print "W", str(xyzw[3])

def CreateXYZKey(xyz):
    key = "X" + str(xyz[0])
    key += "|Y" + str(xyz[1])
    key += "|Z" + str(xyz[2])
    return key

def CreateXYZWKey(xyzw):
    key = "X" + str(xyzw[0])
    key += "|Y" + str(xyzw[1])
    key += "|Z" + str(xyzw[2])
    key += "|W" + str(xyzw[3])
    return key
    
def IsNaN(value):
    return value != value;
    
def NaNToNumber(value, number):
    if IsNaN(value):
        return number
    else:
        return value

def GetConnectedPlugs(plug, incoming, outgoing):
    connectedPlugs = OpenMaya.MPlugArray()
    plug.connectedTo(connectedPlugs, incoming, outgoing)
    return connectedPlugs
    
def GetConnectedPlug(plug, connectedPlugName, connectedPlugType):
    connectedPlugs = OpenMaya.MPlugArray()
    plug.connectedTo(connectedPlugs, True, False)
    for k in range(connectedPlugs.length()):
        if connectedPlugs[k].node().apiType() == connectedPlugType and connectedPlugs[k].partialName(False, False, False, False, False, True) == connectedPlugName:
            return connectedPlugs[k]
    
    return OpenMaya.MPlug()

def PlugValueAsMVector(plug):
    if plug.numChildren() == 3:
        return OpenMaya.MVector(plug.child(0).asMAngle().asDegrees(), plug.child(1).asMAngle().asDegrees(), plug.child(2).asMAngle().asDegrees())
    else:
        return OpenMaya.MVector()
        
def VectorDegreesToRadians(vector):
    return OpenMaya.MVector(OpenMaya.MAngle(vector[0], OpenMaya.MAngle.kDegrees).asRadians(), OpenMaya.MAngle(vector[1], OpenMaya.MAngle.kDegrees).asRadians(), OpenMaya.MAngle(vector[2], OpenMaya.MAngle.kDegrees).asRadians())

def VectorRadiansToDegrees(vector):
    return OpenMaya.MVector(OpenMaya.MAngle(vector[0], OpenMaya.MAngle.kRadians).asDegrees(), OpenMaya.MAngle(vector[1], OpenMaya.MAngle.kRadians).asDegrees(), OpenMaya.MAngle(vector[2], OpenMaya.MAngle.kRadians).asDegrees())

def CreateTransformNodes(nodeName, xmlNode):
    '''
    Creates position, rotation and scale nodes for the node nodeName
    and attaches them to xmlNode
    '''
    print "Getting transform for", nodeName, Cmds.nodeType(nodeName)
    
    position = Cmds.xform(nodeName, q=True, t=True);
    rotation = Cmds.xform(nodeName, q=True, ro=True);
    scale = Cmds.xform(nodeName, q=True, s=True);
    
    if not IsZero(position):
        positionNode = xmlDocument.createElement("Position")
        xmlNode.appendChild(positionNode)
        positionNode.setAttribute("X", str(position[0]))
        positionNode.setAttribute("Y", str(position[1]))
        positionNode.setAttribute("Z", str(position[2]))
    
    if not IsZero(rotation):
        rotationNode = xmlDocument.createElement("Rotation")
        xmlNode.appendChild(rotationNode)
        rotationNode.setAttribute("X", str(rotation[0]))
        rotationNode.setAttribute("Y", str(rotation[1]))
        rotationNode.setAttribute("Z", str(rotation[2]))
    
    if not IsOne(scale):
        scaleNode = xmlDocument.createElement("Scale")
        xmlNode.appendChild(scaleNode)
        scaleNode.setAttribute("X", str(scale[0]))
        scaleNode.setAttribute("Y", str(scale[1]))
        scaleNode.setAttribute("Z", str(scale[2]))

def GetParentName(fullNodePath):
    '''
    Returns the parent's name
    '''
    return fullNodePath.split("|")[-2]

def Bake(minFrame, maxFrame):
    Cmds.bakeResults(sm=True, t=(minFrame, maxFrame), hi="below", sb=1, dic=True, pok=False, sac=False, ral=False, cp=False, shape=False)

def FindIndexOf(list, value, start=0, end=-1):
    '''
    Finds the first occurance of value in [start, end]
    '''
    if end == -1:
        end = len(list)
    
    i = start
    while i <= end:
        if list[i] == value:
            return i
        
        i = i + 1
    
    return end
