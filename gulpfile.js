var fs = require('fs'),
	gulp = require('gulp'),
	rimraf = require('rimraf'),
	concat = require('gulp-concat'),
	gulpif = require('gulp-if');

var mayaScriptsFolder = '/Users/Balki/Documents/maya/2016/scripts/';


gulp.task('Clean', function (cb) {
	rimraf('./Out', cb);
});

gulp.task('Build', ['Clean'], function () {
	gulp.src(['./Scripts/Common.py', './Scripts/Sequencer.py'])
		.pipe(concat('Sequencer.py'))
		.pipe(gulp.dest('./Out/'))
		.pipe(gulpif(function () {
			try {
				var stats = fs.lstatSync(mayaScriptsFolder);
				return stats.isDirectory();
			}
			catch (e) {
				return false;
			}
		}, gulp.dest(mayaScriptsFolder)));
});

gulp.task('default', ['Build']);