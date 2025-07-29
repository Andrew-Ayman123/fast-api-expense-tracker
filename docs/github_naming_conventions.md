# Github Naming Conventions

### Branch Naming Convention

**Format:**

```
<type>/<short-description>
```

**Types (suggested):**

* `feat` – New feature
* `fix` – Bug fix
* `refactor` – Code restructuring without behavior changes
* `test` – Adding or updating tests
* `docs` – Documentation changes
* `ci` – Continuous integration changes

**Examples:**

```
feat/123-user-login
fix/456-api-timeout
docs/789-update-readme
```

---

### Commit Message Convention

**Format:**

```
<type>(<scope>): <short description>

[optional body]
```

**Types:**
Same as branch types (`feat`, `fix`, etc.)

**Examples:**

```
feat(auth): add JWT authentication

fix(api): handle timeout errors in user endpoint

docs(readme): update setup instructions

refactor(user): simplify user role validation logic

fix(ui): resolve navbar overlap on mobile (#123)
```

---

### Pull Request Naming Convention

**Format:**

```
[type] – Short, descriptive title
```

**Examples:**

```
[feat] – Add user authentication with JWT
[fix] – Fix crash on empty search input
[docs] – Improve contribution guidelines
```

**PR Description Template:**

```markdown
### Summary
Brief explanation of the changes.

### Changes
- Added...
- Fixed...
- Removed...

### Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
```

