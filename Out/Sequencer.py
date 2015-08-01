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

'''
Greymind Sequencer for Maya
Version: 1.7.1

(c) 2009 - 2015 Greymind Inc.
    Balakrishnan (Balki) Ranganathan (balki_live_com)
    All Rights Reserved.
'''

# from Common import *
from functools import partial as Partial

SequencerVersion = "1.7.1"

class Animation:
    Id = -1
    Name = ""
    StartFrame = -1
    EndFrame = -1
    Selected = False
    
    def __init__(self, name, startFrame, endFrame, selected=False, id=-1):
        self.Name = name
        self.StartFrame = startFrame
        self.EndFrame = endFrame
        self.Selected = selected
        self.Id = id

class AnimationUI:
    NameTextField = None
    StartFrameTextField = None
    EndFrameTextField = None
    SelectedCheckBox = None
    SetButton = None
    
    Animation = None
    SequencerUI = None
    
    def __init__(self, sequencerUI, animation):
        self.Create(sequencerUI, animation)
        
    def Name_Changed(self, extraArg=None):
        self.Animation.Name = Cmds.textField(self.NameTextField, q=True, text=True)
        self.SequencerUI.Save()
        self.SequencerUI.Update()
        
    def StartFrame_Changed(self, extraArg=None):
        self.Animation.StartFrame = int(Cmds.textField(self.StartFrameTextField, q=True, text=True))
        self.SequencerUI.Save()
        self.SequencerUI.Update()
        
    def EndFrame_Changed(self, extraArg=None):
        self.Animation.EndFrame = int(Cmds.textField(self.EndFrameTextField, q=True, text=True))
        self.SequencerUI.Save()
        self.SequencerUI.Update()
        
    def Select_Changed(self, extraArg=None):
        self.Animation.Selected = Cmds.checkBox(self.SelectedCheckBox, q=True, value=True)
        self.SequencerUI.Save()
        self.SequencerUI.Update()
        
    def Set_Clicked(self, extraArg=None):
        self.SequencerUI.Save()
        self.SequencerUI.Update()
        Cmds.playbackOptions(e=True, min=self.Animation.StartFrame, max=self.Animation.EndFrame)
    
    def Create(self, sequencerUI, animation):
        self.SequencerUI = sequencerUI
        self.Animation = animation
        
        self.SelectedCheckBox = Cmds.checkBox(label='', value=animation.Selected, cc=self.Select_Changed)
        self.NameTextField = Cmds.textField(text=animation.Name, width=183, cc=self.Name_Changed)
        self.StartFrameTextField = Cmds.textField(text=str(animation.StartFrame), cc=self.StartFrame_Changed)
        self.EndFrameTextField = Cmds.textField(text=str(animation.EndFrame), cc=self.EndFrame_Changed)
        self.SetButton = Cmds.button(label='Set', c=self.Set_Clicked)
        
    def Destroy(self):
        Cmds.deleteUI(self.SelectedCheckBox)
        Cmds.deleteUI(self.NameTextField)
        Cmds.deleteUI(self.StartFrameTextField)
        Cmds.deleteUI(self.EndFrameTextField)
    
class Sequencer:
    UniqueId = 0 # Stores the top unique id 
    
    Animations = {} # Stores the animations keyed by a unique id
    Ordering = [] # Stores the order in which the animations are to be displayed by the UI
    
    def GetUniqueId(self):
        self.UniqueId = self.UniqueId + 1
        return (self.UniqueId - 1)
    
    def Count(self):
        if not len(self.Animations) == len(self.Ordering):
            print "Warning: Animations dictionary and Ordering list do not have same number of elements"
        
        return len(self.Animations)
        
    def StartFrame(self):
        startFrame = int(1e6)
        for animationId in self.Animations:
            if self.Animations[animationId].StartFrame < startFrame:
                startFrame = self.Animations[animationId].StartFrame
                
        if startFrame == int(1e6):
            startFrame = 0
        
        return startFrame
    
    def EndFrame(self):
        endFrame = 0
        for animationId in self.Animations:
            if self.Animations[animationId].EndFrame > endFrame:
                endFrame = self.Animations[animationId].EndFrame
                
        return endFrame
        
    def AddAnimationWithId(self, animation):
        self.Animations[animation.Id] = animation
        self.Ordering.append(animation.Id)
        
    def AddAnimation(self, animation):
        # Check if it exists perhaps?
        animation.Id = self.GetUniqueId()
        self.AddAnimationWithId(animation)
        
    def RemoveAnimation(self, animationId):
        del self.Animations[animationId]
        self.Ordering.remove(animationId)
        
class SequencerUI:
    progressBar = ""
    windowName = ""
    windowLayout = ""
    animationsLayout = ""
    buttonsLayout = ""
    startFrameTextBox = ""
    endFrameTextBox = ""
    selectAll = ""
    windowTitle = ""
    width = 0
    height = 0
    sequencer = None
    
    AnimationUIs = {}
    
    def __init__(self):
        self.progressBar = Mel.eval('$tmp = $gMainProgressBar');
        self.windowName = "SequencerWindow"
        self.windowLayout = "SequencerLayout"
        self.animationsLayout = "SequencerAnimations"
        self.buttonsLayout = "SequencerButtons"
        self.selectAll = "SequencerSelectAll"
        self.startFrameTextBox = "SequencerStartFrameTextBox"
        self.endFrameTextBox = "SequencerEndFrameTextBox"
        self.prefixTextBox = "SequencerPrefixTextBox"
        
        self.windowTitle = "Sequencer " + SequencerVersion
        self.width = 400
        self.height = 550
        
        self.Load()
        
    def AttributeName(self, baseNode, attributeName):
        return "%s.%s" % (baseNode, attributeName)
        
    def Load(self):
        '''
        Populate sequencer class from maya nodes
        '''
        Attr = self.AttributeName
        
        self.sequencer = Sequencer()
        
        '''
        self.sequencer.AddAnimation(Animation("Idle", 1, 30))
        self.sequencer.AddAnimation(Animation("Run", 61, 90))
        self.sequencer.AddAnimation(Animation("Walk", 31, 60))
        
        return
        '''
        
        sequencerNode = "SequencerData"
        if not Cmds.objExists(sequencerNode):
            return
            
        self.sequencer.UniqueId = Cmds.getAttr(Attr(sequencerNode, 'UniqueId'))
        ordering = Cmds.getAttr(Attr(sequencerNode, 'Ordering'))
        
        if ordering is None or len(ordering) == 0:
            return
        
        try:
            for orderId in range(len(ordering)):
                animationId = ordering[orderId]
                parentAttribute = Attr(sequencerNode, 'Animation%d' % animationId)
                
                name = Cmds.getAttr(Attr(parentAttribute, "Name%d" % animationId))
                startFrame = Cmds.getAttr(Attr(parentAttribute, "StartFrame%d" % animationId))
                endFrame = Cmds.getAttr(Attr(parentAttribute, "EndFrame%d" % animationId))
                selected = Cmds.getAttr(Attr(parentAttribute, "Selected%d" % animationId))
                
                animation = Animation(name, startFrame, endFrame, selected, animationId)
                self.sequencer.AddAnimationWithId(animation)
        except TypeError:
            print "There seems to be an error loading sequencer data, reseting Sequencer"
            Cmds.delete(sequencerNode)
        
    def Save(self):
        '''
        Save sequencer data back into maya nodes
        '''
        Attr = self.AttributeName
        selection = Cmds.ls(selection=True)
        
        sequencerNode = "SequencerData"
        if Cmds.objExists(sequencerNode):
            Cmds.delete(sequencerNode)
        
        Cmds.createNode('script', name=sequencerNode)
        
        Cmds.addAttr(sequencerNode, longName='UniqueId', attributeType='long', storable=True)
        Cmds.setAttr(Attr(sequencerNode, 'UniqueId'), self.sequencer.UniqueId)
        
        Cmds.addAttr(sequencerNode, longName='Ordering', dataType='Int32Array', storable=True)
        Cmds.setAttr(Attr(sequencerNode, 'Ordering'), self.sequencer.Ordering, type='Int32Array')
        
        if self.sequencer.Count() == 0:
            return
            
        Cmds.addAttr(sequencerNode, longName='Animations', attributeType='compound', numberOfChildren=self.sequencer.Count())
        
        for animation in self.sequencer.Animations.values():
            parentAttribute = Attr(sequencerNode, 'Animation%d' % animation.Id)
            Cmds.addAttr(longName="Animation%d" % animation.Id, attributeType='compound', numberOfChildren=4, parent='Animations')
            Cmds.addAttr(longName="Name%d" % animation.Id, dataType='string', parent='Animation%d' % animation.Id)
            Cmds.addAttr(longName="StartFrame%d" % animation.Id, attributeType='long', parent='Animation%d' % animation.Id)
            Cmds.addAttr(longName="EndFrame%d" % animation.Id, attributeType='long', parent='Animation%d' % animation.Id)
            Cmds.addAttr(longName="Selected%d" % animation.Id, attributeType='bool', parent='Animation%d' % animation.Id)
        
        for animation in self.sequencer.Animations.values():
            parentAttribute = Attr(sequencerNode, 'Animation%d' % animation.Id)
            
            Cmds.setAttr(Attr(parentAttribute, "Name%d" % animation.Id), animation.Name, type='string')
            Cmds.setAttr(Attr(parentAttribute, "StartFrame%d" % animation.Id), animation.StartFrame)
            Cmds.setAttr(Attr(parentAttribute, "EndFrame%d" % animation.Id), animation.EndFrame)
            Cmds.setAttr(Attr(parentAttribute, "Selected%d" % animation.Id), animation.Selected)
            
        #Cmds.select(cl=True)
        if len(selection) > 0:
            Cmds.select(selection)
        
    def CreateAnimationEntry(self, animation):
        '''
        Create the UI entry for the animation
        '''
        Cmds.setParent(self.animationsLayout)
        Cmds.rowLayout(numberOfColumns = 5, columnWidth5 = [35, 185, 50, 50, 35], columnAttach=[1, 'left', 8])
        
        self.AnimationUIs[animation.Id] = AnimationUI(self, animation)
        
    def Refresh(self, extraArg=None):
        '''
        Refreshes the animations UI
        '''
        # Process select all checkbox value
        selected = False
        if Cmds.checkBox(self.selectAll, q=True, exists=True):
            selected = Cmds.checkBox(self.selectAll, q=True, value=True)
        
        if selected == True:
            for animation in self.sequencer.Animations.values():
                if animation.Selected == False:
                    selected = False
                    break
        
        # Clear all UI items
        for animationId in self.AnimationUIs:
            self.AnimationUIs[animationId].Destroy()
        self.AnimationUIs = {}
        
        # Animations Layout
        Cmds.setParent(self.windowLayout)
        if Cmds.columnLayout(self.animationsLayout, exists=True):
            Cmds.deleteUI(self.animationsLayout)
            
        Cmds.columnLayout(self.animationsLayout, adjustableColumn=True)
        
        self.CreateSeparator(self.animationsLayout, 'out')
        
        # Header row
        Cmds.rowLayout(numberOfColumns = 4, columnWidth4 = [35, 185, 50, 50], columnAttach=[1, 'left', 8])
        Cmds.checkBox(self.selectAll, label='', cc=Partial(self.SelectAll), value=selected)
        Cmds.text(label=' Animation Name')
        Cmds.text(label=' Start')
        Cmds.text(label=' End')
        
        self.CreateSeparator(self.animationsLayout, 'out')
        
        # Add back based on order
        
        #print self.sequencer.Ordering
        #return
        
        for orderId in range(len(self.sequencer.Ordering)):
            animationId = self.sequencer.Ordering[orderId]
            self.CreateAnimationEntry(self.sequencer.Animations[animationId])
            
        # Update
        self.Update()
        
        # Save
        self.Save()
        
    def Update(self):
        # Skyrigger tools
        Cmds.textField(self.startFrameTextBox, e=True, text=str(self.sequencer.StartFrame()))
        Cmds.textField(self.endFrameTextBox, e=True, text=str(self.sequencer.EndFrame()))
        
    def MoveUp(self, extraArg=None):
        '''
        Moves a given entry (or a collection of entries) up
        '''
        for index in range(self.sequencer.Count()):
            animation = self.sequencer.Animations[self.sequencer.Ordering[index]]
            if animation.Selected:
                if not index == 0:
                    temp = self.sequencer.Ordering[index - 1]
                    self.sequencer.Ordering[index - 1] = animation.Id
                    self.sequencer.Ordering[index] = temp
        
        self.Refresh()
        
    def MoveDown(self, extraArg=None):
        '''
        Moves a given entry (or a collection of entries) down
        '''
        for index in reversed(range(self.sequencer.Count())):
            animation = self.sequencer.Animations[self.sequencer.Ordering[index]]
            if animation.Selected:
                if not index == self.sequencer.Count() - 1:
                    temp = self.sequencer.Ordering[index + 1]
                    self.sequencer.Ordering[index + 1] = animation.Id
                    self.sequencer.Ordering[index] = temp
        
        self.Refresh()
    
    def SelectAll(self, extraArg=None):
        selected = Cmds.checkBox(self.selectAll, q=True, value=True)
        for animation in self.sequencer.Animations.values():
            animation.Selected = selected
            
        self.Refresh()
        
    def Add(self, extraArg=None):
        self.sequencer.AddAnimation(Animation("", self.sequencer.EndFrame() + 1, self.sequencer.EndFrame() + 30))
        self.Refresh()
        
    def Delete(self, extraArg=None):
        animationsToRemove = []
        for animationId in self.sequencer.Animations.keys():
            if self.sequencer.Animations[animationId].Selected == True:
                animationsToRemove.append(animationId)
                
        for animationId in animationsToRemove:
            self.sequencer.RemoveAnimation(animationId)
            
        self.Refresh()
        
    def SetPlaybackRange(self, startTime, endTime):
        Cmds.playbackOptions(e=True, min=startTime, max=endTime)
        
    def MessageBox(self, dialogMessage, dialogTitle = "Sequencer", dialogButtons=["Ok"]):
        Cmds.confirmDialog(title=dialogTitle, message=dialogMessage, button=dialogButtons)
    
    def CountSelected(self):
        selectedCount = 0
        for animation in self.sequencer.Animations.values():
            if animation.Selected == True:
                selectedCount = selectedCount + 1
        
        return selectedCount
        
    def StartProgressBar(self, statusMessage, maximumValue):
        Cmds.progressBar(self.progressBar, edit=True, beginProgress=True, isInterruptable=True,
            status=statusMessage, maxValue=maximumValue)

    def IsProgressBarCanceled(self):
        if Cmds.progressBar(self.progressBar, query=True, isCancelled=True):
            return True
        else:
            return False
            
    def UpdateProgressBar(self, progress):
        Cmds.progressBar(self.progressBar, edit=True, pr=progress)
    
    def StepProgressBar(self, stepAmount):
        Cmds.progressBar(self.progressBar, edit=True, step=stepAmount)
        
    def EndProgressBar(self):
        Cmds.progressBar(self.progressBar, edit=True, endProgress=True)

    def ImportMoveLister(self, extraArg=None):
        if Cmds.objExists("MoveLister"):        
            totalMoves = Cmds.getAttr("MoveLister.totalMoves")
            for i in range(0, totalMoves):
                nodePrefix = "MoveLister.move" + str(i)

                moveNameNode = nodePrefix + "Name"
                moveName = Cmds.getAttr(moveNameNode)
                
                moveMinNode = nodePrefix + "Min"
                moveMin = Cmds.getAttr(moveMinNode)
                
                moveMaxNode = nodePrefix + "Max"
                moveMax = Cmds.getAttr(moveMaxNode)
                
                self.sequencer.AddAnimation(Animation(moveName, moveMin, moveMax))
            
            self.Refresh()
        else:
            self.MessageBox('MoveLister data not found!')
        
    def PlayblastDisplayEnable(self, enable=True):
        Cmds.setAttr('persp.displayFilmOrigin', enable)
        Cmds.setAttr('persp.displayFilmPivot', enable)
        Cmds.setAttr('persp.displaySafeTitle', enable)
        Cmds.setAttr('persp.displaySafeAction', enable)
        Cmds.setAttr('persp.displayFieldChart', enable)
        Cmds.setAttr('persp.displayResolution', enable)
        Cmds.setAttr('persp.displayFilmGate', enable)
        
    def Export(self, extraArg=None):
        directoryName = os.path.dirname(Cmds.file(q=True, sn=True))
        if not directoryName:
            self.MessageBox('Please save Maya file before exporting.')
            return
            
        selectedCount = self.CountSelected()
        if selectedCount == 0:
            self.MessageBox('Please select animations to export!')
            return
            
        now = datetime.datetime.now()
        exportFilename = "%s/Export %d%d%d-%d%d%d.csv" % (directoryName, now.year, now.month, now.day, now.hour, now.minute, now.second)
        exportFile = open(exportFilename, "w")
        
        exportFile.write("%s, %s, %s\n" % ('Animation Name', 'Start Frame', 'End Frame'))
        for animation in self.sequencer.Animations.values():
            if animation.Selected == True:
                exportFile.write("%s, %d, %d\n" % (animation.Name, animation.StartFrame, animation.EndFrame))
        
        exportFile.close()
        
        choice = Cmds.confirmDialog(title='Export Complete!', message='Do you want to open the file %s now?' % (exportFilename), button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if choice == 'Yes':
            os.startfile(exportFilename)
        
    def GeneratePlayblast(self, extraArg=None):
        prefixText = Cmds.textField(self.prefixTextBox, q=True, text=True)
        if not IsNoneOrEmpty(prefixText):
            prefixText = "%s_" % prefixText
            
        cameraName = 'persp'
        blackThick = 1
        horizontalResolution = 320
        verticalResolution = 240
        scalePercentage = 100
        
        if not Cmds.objExists(cameraName):
            self.MessageBox('Playblast generation requires a camera named %s.' % (cameraName), 'Playblast pre-requisite error')
            return
        
        self.PlayblastDisplayEnable(False)
        
        directoryName = os.path.dirname(Cmds.file(q=True, sn=True))
        if not directoryName:
            self.MessageBox('Please save Maya file before blasting!')
            return
        
        selectedCount = self.CountSelected()
        if selectedCount == 0:
            self.MessageBox('Please select animations to blast!')
            return
            
        self.StartProgressBar('Generating Playblast', selectedCount)
        for animation in self.sequencer.Animations.values():
            if self.IsProgressBarCanceled():
                self.EndProgressBar()
                self.MessageBox('Playblast generation canceled by the user')
                return
                
            if animation.Selected == True:
                self.SetPlaybackRange(animation.StartFrame, animation.EndFrame)
                
                movieFilename = "%s/%s%s" % (directoryName, prefixText, animation.Name.replace("\"", "_").replace("*", "_"))
                Cmds.playblast(format='movie', filename=movieFilename, clearCache=True, viewer=False, showOrnaments=True, fp=4, percent=scalePercentage, compression='none', widthHeight=(horizontalResolution, verticalResolution), fo=True)
                self.StepProgressBar(1)
        
        self.EndProgressBar()
        self.MessageBox('Playblast generation complete!')
        
    def BakeKeys(self, extraArg=None):
        selection = Cmds.ls(selection=True)
        if not len(selection) == 1 or not Cmds.nodeType(selection) == 'joint':
            self.MessageBox('Please select (only) the topmost joint of the skeletal system', 'Bake keys pre-requisite error')
            return
            
        if self.sequencer.EndFrame() > self.sequencer.StartFrame():
            Bake(self.sequencer.StartFrame(), self.sequencer.EndFrame())
            
        self.MessageBox('Bake complete!')
        
    def DeleteRigControls(self, extraArg=None):
        selection = Cmds.ls(selection=True)
        if not len(selection) == 1 or not Cmds.nodeType(selection) == 'joint':
            self.MessageBox('Please select (only) the topmost joint of the skeletal system', 'Delete rig controls pre-requisite error')
            return
            
        controlGroupName = selection[0].replace('Joint_Root', 'Control')
        Cmds.delete(controlGroupName)
        
        skeletonFKGroupName = selection[0].replace('Joint_Root', 'Skeleton_FK')
        Cmds.delete(skeletonFKGroupName)
        
        self.MessageBox('Rig controls deleted!')
        
    def TrimKeys(self, extraArg=None):
        selection = Cmds.ls(selection=True)
        if not len(selection) == 1 or not Cmds.nodeType(selection) == 'joint':
            self.MessageBox('Please select (only) the topmost joint of the skeletal system', 'Trim keys pre-requisite error')
            return
            
        trimStart = int(Cmds.textField(self.startFrameTextBox, q=True, text=True))
        trimEnd = int(Cmds.textField(self.endFrameTextBox, q=True, text=True))
        
        if trimStart < 0:
            self.MessageBox('Trim can start only from 0. Please ensure start frame is valid.', 'Trim keys pre-requisite error')
            
        trimRegions = [0] * (trimEnd + 1)
        for animation in self.sequencer.Animations.values():
            trimRegions[animation.StartFrame:animation.EndFrame + 1] = [1] * (animation.EndFrame - animation.StartFrame + 1)
        
        i = 0
        while i < len(trimRegions):
            tStart = FindIndexOf(trimRegions, 0, i, trimEnd)
            tEnd = FindIndexOf(trimRegions, 1, tStart, trimEnd) - 1
            
            if tEnd < tStart:
                break
            
            Cmds.cutKey(selection, animation='keysOrObjects', option='keys', clear=True, hierarchy='below', time=(tStart,tEnd))
            
            i = tEnd + 1
            i = i + 1
            
        self.MessageBox('Trim complete!')
        
    def GenerateFbx(self, extraArg=None):
        prefixText = Cmds.textField(self.prefixTextBox, q=True, text=True)
        if not IsNoneOrEmpty(prefixText):
            prefixText = "%s_" % prefixText
            
        mayaFile = Cmds.file(q=True, sn=True)
        directoryName = os.path.dirname(mayaFile)
        fileName = os.path.splitext(os.path.basename(mayaFile))[0]
        generatedAnimationFiles = []
        
        createFiles = True
        for animation in self.sequencer.Animations.values():
            if animation.Selected == True:
                negativeStartFrame = -animation.StartFrame
                
                if createFiles == True:
                    Cmds.select(all=True)
                    Cmds.cutKey(time=(self.sequencer.StartFrame() - 10, animation.StartFrame))
                    Cmds.cutKey(time=(animation.EndFrame, self.sequencer.EndFrame() + 10))
                    Cmds.keyframe(edit=True, relative=True, timeChange=negativeStartFrame, time=(animation.StartFrame, animation.EndFrame))
                
                fbxFilename = "%s/%s%s.fbx" % (directoryName, prefixText, animation.Name)
                generatedAnimationFiles.append([animation, fbxFilename])
                
                if createFiles == True:
                    melCode = 'FBXExport -f "%s"' % fbxFilename
                    Mel.eval(melCode)
                
                    Cmds.undo()
                    Cmds.undo()
                    Cmds.undo()
                    Cmds.undo()
            
        # Make sure at least some files were selected
        if len(generatedAnimationFiles) == 0:
            self.MessageBox('Please select at least one animation to export')
            return
        
        # Ready the progress bar
        #self.StartProgressBar('Generating FBX', len(generatedAnimationFiles))
        
        # Open each of these files and stitch them
        masterFilename = "%s/%s%s.fbx" % (directoryName, prefixText, fileName)
        masterFile = open(masterFilename, "w")
        for animationFileIndex in range(len(generatedAnimationFiles)):
            '''
            if self.IsProgressBarCanceled():
                self.EndProgressBar()
                self.MessageBox('FBX generation canceled by user!')
                return
            '''
                
            generatedAnimationFile = generatedAnimationFiles[animationFileIndex]
            generatedAnimation = generatedAnimationFile[0]
            generatedFilename = generatedAnimationFile[1]
            generatedFile = open(generatedFilename, "r")
            
            preTake = True
            inTake = False
            postTake = False
            
            takeString = "Take: \"Take 001\" {"
            endTakeString = "}"
            takeLevel = "    "
            
            for currentLine in generatedFile:
                strippedLine = currentLine.strip(" \r\n")
                
                if not IsNoneOrEmpty(strippedLine):
                    splitLine = currentLine.split(strippedLine)
                else:
                    splitLine = [''] * 2
                    
                lineStartsWith = splitLine[0]
                lineEndsWith = splitLine[1]
                
                if strippedLine == takeString:
                    inTake = True
                    preTake = False
                    takeLevel = lineStartsWith
                    currentLine = currentLine.replace("Take 001", generatedAnimation.Name)
                    
                # For the first file, pick from top of file until the take also
                if animationFileIndex == 0 and preTake == True:
                    masterFile.write(currentLine)
                    
                # For all other files, just cut the take and paste it in
                if inTake == True:
                    masterFile.write(currentLine)
                    
                # For the last file, pick after the take to the bottom of file
                if animationFileIndex == (len(generatedAnimationFiles) - 1) and postTake == True:
                    masterFile.write(currentLine)
                    
                if inTake == True and strippedLine == endTakeString and lineStartsWith == takeLevel:
                    inTake = False
                    postTake = True
                
            #self.StepProgressBar(1)
            
        masterFile.close()
        
        self.MessageBox('FBX generation complete!')
        
    def Create(self):
        '''
        Creates the window
        '''
        if Cmds.window(self.windowName, exists=True):
            Cmds.deleteUI(self.windowName)
        
        # Main window
        Cmds.window(self.windowName, title=self.windowTitle, widthHeight=[self.width, self.height])
        Cmds.scrollLayout(hst = 16, vst = 16)
        Cmds.columnLayout(self.windowLayout)
        
        self.CreateSeparator()
        
        # Buttons
        Cmds.rowLayout(self.buttonsLayout, numberOfColumns = 6, columnWidth6=[30, 48, 55, 75, 75, 75], columnAlign6=['left', 'left', 'left', 'left', 'left', 'left'])
        Cmds.button(label='Add', backgroundColor=[0.6, 0.9, 0.6], c=Partial(self.Add))
        Cmds.button(label='Delete', backgroundColor=[0.9, 0.6, 0.6], c=Partial(self.Delete))
        Cmds.button(label='Move Up', c=Partial(self.MoveUp))
        Cmds.button(label='Move Down', c=Partial(self.MoveDown))
        Cmds.button(label='Refresh', backgroundColor=[0.6, 0.6, 0.9], c=Partial(self.Refresh))
        Cmds.button(label='Export', backgroundColor=[0.6, 0.6, 0.9], c=Partial(self.Export))
        
        self.CreateSeparator()
        
        # Tool controls
        Cmds.frameLayout(label="Tool Controls", collapsable=True, collapse=False)
        Cmds.columnLayout(width = self.width - 5)
        Cmds.rowLayout(numberOfColumns = 2, columnWidth2=[45, 290], columnAlign2=['left', 'left'])
        Cmds.text(label=' Prefix')
        Cmds.textField(self.prefixTextBox, width = 288)
        
        Cmds.setParent('..')
        Cmds.rowLayout(numberOfColumns = 2, columnWidth2=[200, 48], columnAlign2=['left', 'left'])
        Cmds.text(label=' To import from MoveLister')
        Cmds.button(label='Import ML', c=Partial(self.ImportMoveLister), backgroundColor=[0.9, 0.9, 0.8])
        
        Cmds.setParent('..')
        Cmds.rowLayout(numberOfColumns = 2, columnWidth2=[200, 48], columnAlign2=['left', 'left'])
        Cmds.text(label=' To generate multiple playblasts')
        Cmds.button(label='PlayBlast', c=Partial(self.GeneratePlayblast), backgroundColor=[0.9, 0.9, 0.8])
        
        Cmds.setParent('..')
        Cmds.rowLayout(numberOfColumns = 2, columnWidth2=[200, 48], columnAlign2=['left', 'left'])
        Cmds.text(label=' To generate animation-aware FBX')
        Cmds.button(label='Generate FBX', c=Partial(self.GenerateFbx), backgroundColor=[0.9, 0.9, 0.8])
        
        self.CreateSeparator()
        
        # Skyrigger controls
        Cmds.frameLayout(label="Skyrigger and Animation Controls", collapsable=True, collapse=False)
        Cmds.columnLayout(width = self.width - 5)
        Cmds.rowLayout(numberOfColumns = 4, columnWidth4=[60, 55, 55, 55], columnAlign4=['left', 'left', 'left', 'left'])
        Cmds.text(label=' Start frame')
        Cmds.textField(self.startFrameTextBox)
        Cmds.text(label='End frame')
        Cmds.textField(self.endFrameTextBox)
        
        Cmds.setParent('..')
        Cmds.rowLayout(numberOfColumns = 2, columnWidth2=[200, 48], columnAlign2=['left', 'left'])
        Cmds.text(label=' To bake the keys')
        Cmds.button(label='Bake Keys', c=Partial(self.BakeKeys), backgroundColor=[0.8, 0.8, 0.9])
        
        Cmds.setParent('..')
        Cmds.rowLayout(numberOfColumns = 2, columnWidth2=[200, 48], columnAlign2=['left', 'left'])
        Cmds.text(label=' To delete the rig controls')
        Cmds.button(label='Delete Rig Controls', c=Partial(self.DeleteRigControls), backgroundColor=[0.9, 0.8, 0.8])
        
        Cmds.setParent('..')
        Cmds.rowLayout(numberOfColumns = 2, columnWidth2=[200, 48], columnAlign2=['left', 'left'])
        Cmds.text(label=' To trim the keys between moves')
        Cmds.button(label='Trim Keys', c=Partial(self.TrimKeys), backgroundColor=[0.8, 0.9, 0.8])
        
        self.CreateSeparator('..')
        
        self.Refresh()
        
    def CreateSeparator(self, parent=None, separatorStyle='double'):
        '''
        Creates a separator
        '''
        if parent == None:
            parent = self.windowLayout
        
        Cmds.setParent(parent)
        Cmds.separator(style=separatorStyle, width=1)
        
    def Show(self):
        Cmds.showWindow(self.windowName)

def Run():
    sequencerUI = SequencerUI()
    sequencerUI.Create()
    sequencerUI.Show()
