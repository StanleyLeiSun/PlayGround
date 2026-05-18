## ADDED Requirements

### Requirement: Check in a written task with photo
The system SHALL require photo upload when checking in a written-type task.

#### Scenario: Successful check-in with photo
- **WHEN** user submits check-in for a written task with a photo file (JPEG/PNG, max 1MB after compression)
- **THEN** system marks the daily task as done, stores the photo, records completed_at timestamp and completed_by user ID, and triggers point awarding

#### Scenario: Check-in without photo for written task
- **WHEN** user submits check-in for a written task without a photo
- **THEN** system returns error 400 indicating photo is required for written tasks

### Requirement: Check in a reading task without mandatory photo
The system SHALL allow checking in a reading-type task with or without a photo.

#### Scenario: Check-in reading task without photo
- **WHEN** user submits check-in for a reading task without a photo
- **THEN** system marks the task as done, records completed_at and completed_by

#### Scenario: Check-in reading task with optional photo
- **WHEN** user submits check-in for a reading task with a photo
- **THEN** system marks the task as done and stores the photo

### Requirement: Prevent duplicate check-in
The system SHALL not allow checking in an already-completed task.

#### Scenario: Duplicate check-in attempt
- **WHEN** user attempts to check in a task with status "done"
- **THEN** system returns error 409 indicating task already completed

### Requirement: Photo storage and retrieval
The system SHALL store photos organized by family/child/date and provide authenticated access.

#### Scenario: Photo upload
- **WHEN** a photo is uploaded during check-in
- **THEN** system stores it at path /{family_id}/{child_id}/{date}/{uuid}.jpg and creates a check_in_photo record

#### Scenario: Photo retrieval
- **WHEN** an authenticated family member requests a photo
- **THEN** system returns the photo file with proper content-type header

#### Scenario: Unauthorized photo access
- **WHEN** a user from a different family attempts to access the photo
- **THEN** system returns error 403

### Requirement: Record operator identity
The system SHALL record which user performed the check-in.

#### Scenario: Grandparent checks in
- **WHEN** a grandparent completes a check-in
- **THEN** the daily_task.completed_by field stores the grandparent's user ID

#### Scenario: Parent checks in
- **WHEN** a parent completes a check-in
- **THEN** the daily_task.completed_by field stores the parent's user ID
