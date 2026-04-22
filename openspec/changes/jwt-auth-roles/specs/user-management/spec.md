# User Management Specification

## Purpose

Define user profile management with role-based assignments. The system MUST support hardcoded users with predefined roles for initial deployment and testing.

## Functional Requirements

### Requirement: User Profile Model

The system MUST maintain a UserProfile model extending the Django User model with role information.

#### Scenario: User profile created for new user

- GIVEN a Django User exists with email "manager1@uniwell.com"
- WHEN the user management system initializes
- THEN a UserProfile MUST exist for this user
- AND the UserProfile MUST have a OneToOne relationship with the User
- AND the UserProfile MUST contain a role field

#### Scenario: Profile role is accessible via user relationship

- GIVEN a UserProfile exists with role "manager" linked to User "manager1@uniwell.com"
- WHEN accessing the user through the system
- THEN the user's profile MUST be accessible via user.profile
- AND the role MUST be accessible via user.profile.role

---

### Requirement: Role Enumeration

The system MUST support exactly two roles: "manager" and "operator".

#### Scenario: Valid manager role assignment

- GIVEN a user exists
- WHEN assigning role "manager" to the user's profile
- THEN the assignment MUST succeed
- AND the role MUST be stored as "manager"

#### Scenario: Valid operator role assignment

- GIVEN a user exists
- WHEN assigning role "operator" to the user's profile
- THEN the assignment MUST succeed
- AND the role MUST be stored as "operator"

#### Scenario: Invalid role assignment rejected

- GIVEN a user exists
- WHEN attempting to assign role "admin" to the user's profile
- THEN the assignment MUST be rejected
- AND a validation error MUST be raised

#### Scenario: Null role rejected

- GIVEN a user exists
- WHEN attempting to set role to NULL or empty string
- THEN the assignment MUST be rejected
- AND a validation error MUST indicate role is required

---

### Requirement: Hardcoded Users

The system MUST provide a management command to seed 6 hardcoded users with specific emails and predefined roles.

#### Scenario: Seed command creates all 6 users

- GIVEN the database has no users
- WHEN running the management command `python manage.py seed_auth_users`
- THEN exactly 6 users MUST be created
- AND each user MUST have an associated UserProfile
- AND each UserProfile MUST have a valid role assigned

#### Scenario: Manager users are created correctly

- GIVEN the seed command has been executed
- THEN the following users MUST exist with role "manager":
  - manager1@uniwell.com
  - manager2@uniwell.com
  - manager3@uniwell.com
  - manager4@uniwell.com

#### Scenario: Operator users are created correctly

- GIVEN the seed command has been executed
- THEN the following users MUST exist with role "operator":
  - operator1@uniwell.com
  - operator2@uniwell.com

#### Scenario: All seeded users have default password

- GIVEN the seed command has been executed
- THEN all 6 users MUST be able to authenticate with password "password123"

#### Scenario: Idempotent seed operation

- GIVEN the seed command has already been executed
- WHEN running the seed command again
- THEN no duplicate users MUST be created
- AND existing users MUST not be modified
- AND the command MUST complete successfully

#### Scenario: Partial seed handling

- GIVEN some of the 6 users already exist (e.g., manager1@uniwell.com)
- WHEN running the seed command
- THEN the existing users MUST be skipped
- AND the remaining users MUST be created
- AND existing user data MUST not be modified

---

### Requirement: User Data Integrity

The system MUST maintain data integrity for user profiles.

#### Scenario: User deletion cascades to profile

- GIVEN a User exists with an associated UserProfile
- WHEN the User is deleted
- THEN the associated UserProfile MUST also be deleted
- AND no orphaned UserProfile records MUST remain

#### Scenario: Profile deletion does not delete user

- GIVEN a User exists with an associated UserProfile
- WHEN the UserProfile is deleted
- THEN the User MAY remain in the database
- AND the behavior SHOULD be configurable

---

## Non-Functional Requirements

### Requirement: Database Schema

The UserProfile model MUST use appropriate database constraints.

#### Scenario: OneToOne constraint enforced

- GIVEN a User "manager1@uniwell.com" has a UserProfile
- WHEN attempting to create a second UserProfile for the same User
- THEN the database MUST reject the operation
- AND an integrity error MUST be raised

#### Scenario: Role field has appropriate length

- GIVEN the UserProfile role field
- THEN the field MUST support at least 20 characters
- AND the field SHOULD use a CharField with choices constraint

---

### Requirement: User Management Performance

The user management operations SHOULD perform efficiently.

#### Scenario: Seed command completes quickly

- GIVEN an empty database
- WHEN running the seed command
- THEN the command SHOULD complete in less than 5 seconds
- AND the command MUST complete in less than 30 seconds

#### Scenario: Profile lookup performance

- GIVEN a user accessing their profile
- WHEN the system retrieves the user profile
- THEN the query SHOULD execute in less than 100ms
- AND the query SHOULD use the OneToOne relationship index

---

## Error Handling Requirements

### Requirement: Seed Command Error Handling

The seed command MUST handle errors gracefully.

#### Scenario: Database connection error

- GIVEN the database is unavailable
- WHEN running the seed command
- THEN the command MUST exit with a non-zero status code
- AND the error message MUST indicate the connection failure

#### Scenario: Permission denied

- GIVEN the database user lacks INSERT permissions
- WHEN running the seed command
- THEN the command MUST exit with a non-zero status code
- AND the error message MUST indicate the permission issue

---

## Edge Cases

### Requirement: Edge Case Handling

The system MUST handle user management edge cases gracefully.

#### Scenario: User with same email in different case

- GIVEN a user exists with email "Manager1@uniwell.com"
- WHEN attempting to create a user with email "manager1@uniwell.com"
- THEN the system MUST treat these as the same email (case-insensitive)
- AND no duplicate user MUST be created

#### Scenario: Very long email addresses

- GIVEN an email address of 254 characters (RFC 5321 limit)
- WHEN creating a user with this email
- THEN the operation MUST succeed
- AND the email MUST be stored correctly

#### Scenario: Special characters in email

- GIVEN an email with valid special characters (e.g., "user+tag@uniwell.com")
- WHEN creating a user with this email
- THEN the operation MUST succeed
- AND the email MUST be stored correctly

#### Scenario: Unicode email handling

- GIVEN an email with Unicode characters (e.g., "用户@例子.测试")
- WHEN creating a user with this email
- THEN the operation SHOULD succeed
- OR the system MUST provide a clear error message if not supported
