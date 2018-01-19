
# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).

## [Unreleased]

### Added
 
- Trigger course grading on click if scoped to Course.  Course grading only occurs in LMS. Course grading is done via certificate generation.  At present, the only marker of a completed course for open-ended courses (courses with no end date) is a GeneratedCertificate object.  This creates one.  
- Disable button once clicked if scoped to Course (can't uncomplete a Course).
- Add Scope field with Block and Course options.
- Add fields for before and after text, so button text is editable.
- Add instruction field for additional information. 
- Add a Studio editing view.
- Scope all fields to `Scope.content`, not `Scope.settings`.
