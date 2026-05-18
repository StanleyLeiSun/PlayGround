## ADDED Requirements

### Requirement: User registration
The system SHALL allow new users to register with phone number and password, creating a new family upon registration.

#### Scenario: Parent registers and creates family
- **WHEN** a new user provides phone number, password, and family name
- **THEN** system creates a user account with role "parent", creates a family entity, and returns JWT tokens

#### Scenario: Duplicate phone number
- **WHEN** a user attempts to register with an already registered phone number
- **THEN** system returns error 409 with message indicating phone already exists

### Requirement: User login
The system SHALL authenticate users via phone number and password, returning JWT tokens.

#### Scenario: Successful login
- **WHEN** user provides valid phone number and password
- **THEN** system returns access token (7-day expiry) and refresh token (30-day expiry)

#### Scenario: Invalid credentials
- **WHEN** user provides incorrect password
- **THEN** system returns error 401

### Requirement: Family invitation
The system SHALL allow parents to generate invite codes for grandparents to join the family.

#### Scenario: Generate invite code
- **WHEN** a parent requests an invite code
- **THEN** system generates a 6-character alphanumeric code with 24-hour expiry

#### Scenario: Grandparent joins family
- **WHEN** a registered user submits a valid invite code
- **THEN** user is added to the family with role "grandparent"

#### Scenario: Expired invite code
- **WHEN** a user submits an invite code older than 24 hours
- **THEN** system returns error 410 indicating code expired

### Requirement: Child profile management
The system SHALL allow parents to create, update, and delete child profiles within their family.

#### Scenario: Create child profile
- **WHEN** a parent provides child name and age
- **THEN** system creates a child record linked to the family with a point account initialized at 0

#### Scenario: Update child profile
- **WHEN** a parent updates a child's name or age
- **THEN** system persists the changes

#### Scenario: Delete child profile
- **WHEN** a parent deletes a child profile
- **THEN** system soft-deletes the child and all associated data (templates, daily tasks, points)

### Requirement: Role-based access control
The system SHALL restrict certain operations to parent role only.

#### Scenario: Grandparent attempts parent-only action
- **WHEN** a grandparent user attempts to create/modify task templates, manage rewards, or invite members
- **THEN** system returns error 403

#### Scenario: Parent accesses all features
- **WHEN** a parent user accesses any endpoint
- **THEN** system allows the operation (parents have superset of grandparent permissions)
