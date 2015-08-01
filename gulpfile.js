var gulp = require("gulp"),
	rimraf = require("rimraf"),
	concat = require("gulp-concat");

gulp.task('Clean', function (cb) {
	rimraf('./Out', cb);
});

gulp.task('Build', ['Clean'], function () {
	gulp.src(['./Scripts/Common.py', './Scripts/Sequencer.py'])
		.pipe(concat('Sequencer.py'))
		.pipe(gulp.dest('./Out/'));
});

gulp.task('default', ['Build']);