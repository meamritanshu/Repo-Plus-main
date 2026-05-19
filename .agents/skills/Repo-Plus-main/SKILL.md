```markdown
# Repo-Plus-main Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `Repo-Plus-main` JavaScript codebase. It covers file naming, import/export styles, commit message conventions, and testing practices. By following these guidelines, contributors can maintain consistency and quality across the project.

## Coding Conventions

### File Naming
- Use **camelCase** for all file names.
  - Example: `userProfile.js`, `dataFetcher.test.js`

### Import Style
- Use **relative imports** for modules within the project.
  - Example:
    ```javascript
    import { fetchData } from './dataFetcher';
    ```

### Export Style
- Use **named exports** for all modules.
  - Example:
    ```javascript
    // In dataFetcher.js
    export function fetchData() { ... }
    ```

### Commit Messages
- Use **conventional commit** format.
- Prefix test-related commits with `test`.
- Keep commit messages concise (average ~76 characters).
  - Example:
    ```
    test: add unit tests for user authentication module
    ```

## Workflows

### Adding a New Module
**Trigger:** When you need to add a new feature or utility.
**Command:** `/add-module`

1. Create a new file using camelCase (e.g., `newFeature.js`).
2. Implement your feature using named exports.
    ```javascript
    // newFeature.js
    export function newFeature() { ... }
    ```
3. Import the module where needed using a relative path.
    ```javascript
    import { newFeature } from './newFeature';
    ```
4. Write corresponding tests in a file named `newFeature.test.js`.

### Writing and Running Tests
**Trigger:** When you need to test new or existing functionality.
**Command:** `/run-tests`

1. Create a test file with the pattern `*.test.js` (e.g., `dataFetcher.test.js`).
2. Write your tests using the project's preferred (but unspecified) testing framework.
3. Run the tests using the appropriate command for the chosen framework.

### Committing Changes
**Trigger:** When you are ready to commit your work.
**Command:** `/commit-changes`

1. Write a commit message using the conventional format.
    - For tests: `test: describe what the test covers`
    - For features: `<type>: short description`
2. Keep the message concise and descriptive.

## Testing Patterns

- Test files follow the `*.test.js` naming convention.
- Each module should have a corresponding test file.
- The specific testing framework is not specified; follow general JavaScript testing best practices.

  Example test file:
  ```javascript
  // dataFetcher.test.js
  import { fetchData } from './dataFetcher';

  test('fetchData returns expected data', () => {
    // Test implementation
  });
  ```

## Commands
| Command         | Purpose                                 |
|-----------------|-----------------------------------------|
| /add-module     | Scaffold a new module with conventions  |
| /run-tests      | Run all test files in the project       |
| /commit-changes | Commit changes using proper conventions |
```
