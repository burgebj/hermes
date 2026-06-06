"""ECC ecc-java-kotlin -- Hermes plugin.

Provides 23 skills:
  - agent-java-build-resolver
  - agent-java-reviewer
  - agent-kotlin-build-resolver
  - agent-kotlin-reviewer
  - android-clean-architecture
  - cmd-gradle-build
  - cmd-kotlin-build
  - cmd-kotlin-review
  - cmd-kotlin-test
  - compose-multiplatform-patterns
  - java-coding-standards
  - jpa-patterns
  - kotlin-coroutines-flows
  - kotlin-exposed-patterns
  - kotlin-ktor-patterns
  - kotlin-patterns
  - kotlin-testing
  - rules-java
  - rules-kotlin
  - springboot-patterns
  - springboot-security
  - springboot-tdd
  - springboot-verification
"""

from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_SKILLS_DIR = _PLUGIN_DIR / "skills"

SKILLS = [
    "agent-java-build-resolver",
        "agent-java-reviewer",
        "agent-kotlin-build-resolver",
        "agent-kotlin-reviewer",
        "android-clean-architecture",
        "cmd-gradle-build",
        "cmd-kotlin-build",
        "cmd-kotlin-review",
        "cmd-kotlin-test",
        "compose-multiplatform-patterns",
        "java-coding-standards",
        "jpa-patterns",
        "kotlin-coroutines-flows",
        "kotlin-exposed-patterns",
        "kotlin-ktor-patterns",
        "kotlin-patterns",
        "kotlin-testing",
        "rules-java",
        "rules-kotlin",
        "springboot-patterns",
        "springboot-security",
        "springboot-tdd",
        "springboot-verification",
]


def register(ctx):
    """Register all ecc-java-kotlin skills and commands."""
    for skill in SKILLS:
        skill_path = _SKILLS_DIR / f"{skill}.md"
        if skill_path.exists():
            ctx.register_skill(
                name=skill,
                path=skill_path,
                description=f"ECC: {skill}",
            )

        # Register /kotlin-build slash command
    def _handle_kotlin_build(raw_args: str) -> str:
        return '---\ndescription: Fix Kotlin/Gradle build errors, compiler warnings, and dependency issues incrementally. Invokes the kotlin-build-resolver agent for minimal, surgical fixes.\n---\n\n# Kotlin Build and Fix\n\nThis command invokes the **kotlin-build-resolver** agent to incrementally fix Kotlin build errors with minimal changes.\n\n## What This Command Does\n\n1. **Run Diagnostics**: Execute `./gradlew build`, `detekt`, `ktlintCheck`\n2. **Parse Errors**: Group by file and sort by severity\n3. **Fix Incrementally**: One error at a time\n4. **Verify Each Fix**: Re-run build after each change\n5. **Report Summary**: Show what was fixed and what remains\n\n## When to Use\n\nUse `/kotlin-build` when:\n- `./gradlew build` fails with errors\n- Kotlin compiler reports errors\n- `./gradlew detekt` reports violations\n- Gradle dependency resolution fails\n- After pulling changes that break the build\n\n## Diagnostic Commands Run\n\n```bash\n# Primary build check\n./gradlew build 2>&1\n\n# Static analysis\n./gradlew detekt 2>&1 || echo "detekt not configured"\n./gradlew ktlintCheck 2>&1 || echo "ktlint not configured"\n\n# Dependency issues\n./gradlew dependencies --configuration runtimeClasspath 2>&1 | head -100\n\n# Optional deep refresh when caches or dependency metadata are suspect\n./gradlew build --refresh-dependencies\n```\n\n## Example Session\n\n````text\nUser: /kotlin-build\n\nAgent:\n# Kotlin Build Resolution\n\n## Initial Diagnostics\n\n```bash\n$ ./gradlew build\ne: src/main/kotlin/com/example/service/UserService.kt:25:15 Unresolved reference: UserRepository\ne: src/main/kotlin/com/example/routes/UserRoutes.kt:42:9 Type mismatch: inferred type is String but Int was expected\ne: src/main/kotlin/com/example/routes/UserRoutes.kt:58:5 \'when\' expression must be exhaustive\n```\n\nErrors found: 3\n\n## Fix 1: Unresolved Reference\n\nFile: src/main/kotlin/com/example/service/UserService.kt:25\nError: Unresolved reference: UserRepository\nCause: Missing import\n\n```kotlin\n// Added import\nimport com.example.repository.UserRepository\n```\n\n```bash\n$ ./gradlew build\n# 2 errors remaining\n```\n\n## Fix 2: Type Mismatch\n\nFile: src/main/kotlin/com/example/routes/UserRoutes.kt:42\nError: Type mismatch: inferred type is String but Int was expected\n\n```kotlin\n// Changed\nval count = call.parameters["count"]\n// To\nval count = call.parameters["count"]?.toIntOrNull()\n    ?: return@get call.respond(HttpStatusCode.BadRequest, "Invalid count")\n```\n\n```bash\n$ ./gradlew build\n# 1 error remaining\n```\n\n## Fix 3: Non-Exhaustive When\n\nFile: src/main/kotlin/com/example/routes/UserRoutes.kt:58\nError: \'when\' expression must be exhaustive\n\n```kotlin\n// Added missing branch\nwhen (user.role) {\n    Role.ADMIN -> handleAdmin(user)\n    Role.USER -> handleUser(user)\n    Role.MODERATOR -> handleModerator(user) // Added\n}\n```\n\n```bash\n$ ./gradlew build\n# Build successful!\n```\n\n## Final Verification\n\n```bash\n$ ./gradlew detekt\n# No issues\n\n$ ./gradlew test\n# All tests passed\n```\n\n## Summary\n\n| Metric | Count |\n|--------|-------|\n| Build errors fixed | 3 |\n| Detekt issues fixed | 0 |\n| Files modified | 2 |\n| Remaining issues | 0 |\n\nBuild Status: PASS: SUCCESS\n````\n\n## Common Errors Fixed\n\n| Error | Typical Fix |\n|-------|-------------|\n| `Unresolved reference: X` | Add import or dependency |\n| `Type mismatch` | Fix type conversion or assignment |\n| `\'when\' must be exhaustive` | Add missing sealed class branches |\n| `Suspend function can only be called from coroutine` | Add `suspend` modifier |\n| `Smart cast impossible` | Use local `val` or `let` |\n| `None of the following candidates is applicable` | Fix argument types |\n| `Could not resolve dependency` | Fix version or add repository |\n\n## Fix Strategy\n\n1. **Build errors first** - Code must compile\n2. **Detekt violations second** - Fix code quality issues\n3. **ktlint warnings third** - Fix formatting\n4. **One fix at a time** - Verify each change\n5. **Minimal changes** - Don\'t refactor, just fix\n\n## Stop Conditions\n\nThe agent will stop and report if:\n- Same error persists after 3 attempts\n- Fix introduces more errors\n- Requires architectural changes\n- Missing external dependencies\n\n## Related Commands\n\n- `/kotlin-test` - Run tests after build succeeds\n- `/kotlin-review` - Review code quality\n- `verification-loop` skill - Full verification loop\n\n## Related\n\n- Agent: `agents/kotlin-build-resolver.md`\n- Skill: `skills/kotlin-patterns/`\n'
    ctx.register_command(
        name="kotlin-build",
        handler=_handle_kotlin_build,
        description="ECC /kotlin-build command",
    )


    # Register /kotlin-review slash command
    def _handle_kotlin_review(raw_args: str) -> str:
        return '---\ndescription: Comprehensive Kotlin code review for idiomatic patterns, null safety, coroutine safety, and security. Invokes the kotlin-reviewer agent.\n---\n\n# Kotlin Code Review\n\nThis command invokes the **kotlin-reviewer** agent for comprehensive Kotlin-specific code review.\n\n## What This Command Does\n\n1. **Identify Kotlin Changes**: Find modified `.kt` and `.kts` files via `git diff`\n2. **Run Build & Static Analysis**: Execute `./gradlew build`, `detekt`, `ktlintCheck`\n3. **Security Scan**: Check for SQL injection, command injection, hardcoded secrets\n4. **Null Safety Review**: Analyze `!!` usage, platform type handling, unsafe casts\n5. **Coroutine Review**: Check structured concurrency, dispatcher usage, cancellation\n6. **Generate Report**: Categorize issues by severity\n\n## When to Use\n\nUse `/kotlin-review` when:\n- After writing or modifying Kotlin code\n- Before committing Kotlin changes\n- Reviewing pull requests with Kotlin code\n- Onboarding to a new Kotlin codebase\n- Learning idiomatic Kotlin patterns\n\n## Review Categories\n\n### CRITICAL (Must Fix)\n- SQL/Command injection vulnerabilities\n- Force-unwrap `!!` without justification\n- Platform type null safety violations\n- GlobalScope usage (structured concurrency violation)\n- Hardcoded credentials\n- Unsafe deserialization\n\n### HIGH (Should Fix)\n- Mutable state where immutable suffices\n- Blocking calls inside coroutine context\n- Missing cancellation checks in long loops\n- Non-exhaustive `when` on sealed types\n- Large functions (>50 lines)\n- Deep nesting (>4 levels)\n\n### MEDIUM (Consider)\n- Non-idiomatic Kotlin (Java-style patterns)\n- Missing trailing commas\n- Scope function misuse or nesting\n- Missing sequence for large collection chains\n- Redundant explicit types\n\n## Automated Checks Run\n\n```bash\n# Build check\n./gradlew build\n\n# Static analysis\n./gradlew detekt\n\n# Formatting check\n./gradlew ktlintCheck\n\n# Tests\n./gradlew test\n```\n\n## Example Usage\n\n````text\nUser: /kotlin-review\n\nAgent:\n# Kotlin Code Review Report\n\n## Files Reviewed\n- src/main/kotlin/com/example/service/UserService.kt (modified)\n- src/main/kotlin/com/example/routes/UserRoutes.kt (modified)\n\n## Static Analysis Results\n✓ Build: Successful\n✓ detekt: No issues\nWARNING: ktlint: 2 formatting warnings\n\n## Issues Found\n\n[CRITICAL] Force-Unwrap Null Safety\nFile: src/main/kotlin/com/example/service/UserService.kt:28\nIssue: Using !! on nullable repository result\n```kotlin\nval user = repository.findById(id)!!  // NPE risk\n```\nFix: Use safe call with error handling\n```kotlin\nval user = repository.findById(id)\n    ?: throw UserNotFoundException("User $id not found")\n```\n\n[HIGH] GlobalScope Usage\nFile: src/main/kotlin/com/example/routes/UserRoutes.kt:45\nIssue: Using GlobalScope breaks structured concurrency\n```kotlin\nGlobalScope.launch {\n    notificationService.sendWelcome(user)\n}\n```\nFix: Use the call\'s coroutine scope\n```kotlin\nlaunch {\n    notificationService.sendWelcome(user)\n}\n```\n\n## Summary\n- CRITICAL: 1\n- HIGH: 1\n- MEDIUM: 0\n\nRecommendation: FAIL: Block merge until CRITICAL issue is fixed\n````\n\n## Approval Criteria\n\n| Status | Condition |\n|--------|-----------|\n| PASS: Approve | No CRITICAL or HIGH issues |\n| WARNING: Warning | Only MEDIUM issues (merge with caution) |\n| FAIL: Block | CRITICAL or HIGH issues found |\n\n## Integration with Other Commands\n\n- Use `/kotlin-test` first to ensure tests pass\n- Use `/kotlin-build` if build errors occur\n- Use `/kotlin-review` before committing\n- Use `/code-review` for non-Kotlin-specific concerns\n\n## Related\n\n- Agent: `agents/kotlin-reviewer.md`\n- Skills: `skills/kotlin-patterns/`, `skills/kotlin-testing/`\n'
    ctx.register_command(
        name="kotlin-review",
        handler=_handle_kotlin_review,
        description="ECC /kotlin-review command",
    )


    # Register /kotlin-test slash command
    def _handle_kotlin_test(raw_args: str) -> str:
        return '---\ndescription: Enforce TDD workflow for Kotlin. Write Kotest tests first, then implement. Verify 80%+ coverage with Kover.\n---\n\n# Kotlin TDD Command\n\nThis command enforces test-driven development methodology for Kotlin code using Kotest, MockK, and Kover.\n\n## What This Command Does\n\n1. **Define Types/Interfaces**: Scaffold function signatures first\n2. **Write Kotest Tests**: Create comprehensive test specs (RED)\n3. **Run Tests**: Verify tests fail for the right reason\n4. **Implement Code**: Write minimal code to pass (GREEN)\n5. **Refactor**: Improve while keeping tests green\n6. **Check Coverage**: Ensure 80%+ coverage with Kover\n\n## When to Use\n\nUse `/kotlin-test` when:\n- Implementing new Kotlin functions or classes\n- Adding test coverage to existing Kotlin code\n- Fixing bugs (write failing test first)\n- Building critical business logic\n- Learning TDD workflow in Kotlin\n\n## TDD Cycle\n\n```\nRED     -> Write failing Kotest test\nGREEN   -> Implement minimal code to pass\nREFACTOR -> Improve code, tests stay green\nREPEAT  -> Next test case\n```\n\n## Example Session\n\n````text\nUser: /kotlin-test I need a function to validate user registration requests\n\nAgent:\n# TDD Session: Registration Validator\n\n## Step 1: Define Interface\n\n```kotlin\n// validator/RegistrationValidator.kt\npackage com.example.validator\n\ndata class RegistrationRequest(\n    val name: String,\n    val email: String,\n    val password: String,\n)\n\nsealed class ValidationResult {\n    data object Valid : ValidationResult()\n    data class Invalid(val errors: List<String>) : ValidationResult()\n}\n\nfun validateRegistration(request: RegistrationRequest): ValidationResult {\n    TODO("not implemented")\n}\n```\n\n## Step 2: Write Kotest Tests (RED)\n\n```kotlin\n// validator/RegistrationValidatorTest.kt\npackage com.example.validator\n\nimport io.kotest.core.spec.style.FunSpec\nimport io.kotest.matchers.shouldBe\nimport io.kotest.matchers.types.shouldBeInstanceOf\n\nclass RegistrationValidatorTest : FunSpec({\n    test("valid registration returns Valid") {\n        val request = RegistrationRequest(\n            name = "Alice",\n            email = "alice@example.com",\n            password = "SecureP@ss1",\n        )\n\n        val result = validateRegistration(request)\n\n        result.shouldBeInstanceOf<ValidationResult.Valid>()\n    }\n\n    test("blank name returns Invalid") {\n        val request = RegistrationRequest(\n            name = "",\n            email = "alice@example.com",\n            password = "SecureP@ss1",\n        )\n\n        val result = validateRegistration(request)\n\n        val invalid = result.shouldBeInstanceOf<ValidationResult.Invalid>()\n        invalid.errors shouldBe listOf("Name is required")\n    }\n\n    test("invalid email returns Invalid") {\n        val request = RegistrationRequest(\n            name = "Alice",\n            email = "not-an-email",\n            password = "SecureP@ss1",\n        )\n\n        val result = validateRegistration(request)\n\n        val invalid = result.shouldBeInstanceOf<ValidationResult.Invalid>()\n        invalid.errors shouldBe listOf("Invalid email format")\n    }\n\n    test("short password returns Invalid") {\n        val request = RegistrationRequest(\n            name = "Alice",\n            email = "alice@example.com",\n            password = "short",\n        )\n\n        val result = validateRegistration(request)\n\n        val invalid = result.shouldBeInstanceOf<ValidationResult.Invalid>()\n        invalid.errors shouldBe listOf("Password must be at least 8 characters")\n    }\n\n    test("multiple errors returns all errors") {\n        val request = RegistrationRequest(\n            name = "",\n            email = "bad",\n            password = "short",\n        )\n\n        val result = validateRegistration(request)\n\n        val invalid = result.shouldBeInstanceOf<ValidationResult.Invalid>()\n        invalid.errors.size shouldBe 3\n    }\n})\n```\n\n## Step 3: Run Tests - Verify FAIL\n\n```bash\n$ ./gradlew test\n\nRegistrationValidatorTest > valid registration returns Valid FAILED\n  kotlin.NotImplementedError: An operation is not implemented\n\nFAILED (5 tests, 0 passed, 5 failed)\n```\n\n✓ Tests fail as expected (NotImplementedError).\n\n## Step 4: Implement Minimal Code (GREEN)\n\n```kotlin\n// validator/RegistrationValidator.kt\npackage com.example.validator\n\nprivate val EMAIL_REGEX = Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}$")\nprivate const val MIN_PASSWORD_LENGTH = 8\n\nfun validateRegistration(request: RegistrationRequest): ValidationResult {\n    val errors = buildList {\n        if (request.name.isBlank()) add("Name is required")\n        if (!EMAIL_REGEX.matches(request.email)) add("Invalid email format")\n        if (request.password.length < MIN_PASSWORD_LENGTH) add("Password must be at least $MIN_PASSWORD_LENGTH characters")\n    }\n\n    return if (errors.isEmpty()) ValidationResult.Valid\n    else ValidationResult.Invalid(errors)\n}\n```\n\n## Step 5: Run Tests - Verify PASS\n\n```bash\n$ ./gradlew test\n\nRegistrationValidatorTest > valid registration returns Valid PASSED\nRegistrationValidatorTest > blank name returns Invalid PASSED\nRegistrationValidatorTest > invalid email returns Invalid PASSED\nRegistrationValidatorTest > short password returns Invalid PASSED\nRegistrationValidatorTest > multiple errors returns all errors PASSED\n\nPASSED (5 tests, 5 passed, 0 failed)\n```\n\n✓ All tests passing!\n\n## Step 6: Check Coverage\n\n```bash\n$ ./gradlew koverHtmlReport\n\nCoverage: 100.0% of statements\n```\n\n✓ Coverage: 100%\n\n## TDD Complete!\n````\n\n## Test Patterns\n\n### StringSpec (Simplest)\n\n```kotlin\nclass CalculatorTest : StringSpec({\n    "add two positive numbers" {\n        Calculator.add(2, 3) shouldBe 5\n    }\n})\n```\n\n### BehaviorSpec (BDD)\n\n```kotlin\nclass OrderServiceTest : BehaviorSpec({\n    Given("a valid order") {\n        When("placed") {\n            Then("should be confirmed") { /* ... */ }\n        }\n    }\n})\n```\n\n### Data-Driven Tests\n\n```kotlin\nclass ParserTest : FunSpec({\n    context("valid inputs") {\n        withData("2026-01-15", "2026-12-31", "2000-01-01") { input ->\n            parseDate(input).shouldNotBeNull()\n        }\n    }\n})\n```\n\n### Coroutine Testing\n\n```kotlin\nclass AsyncServiceTest : FunSpec({\n    test("concurrent fetch completes") {\n        runTest {\n            val result = service.fetchAll()\n            result.shouldNotBeEmpty()\n        }\n    }\n})\n```\n\n## Coverage Commands\n\n```bash\n# Run tests with coverage\n./gradlew koverHtmlReport\n\n# Verify coverage thresholds\n./gradlew koverVerify\n\n# XML report for CI\n./gradlew koverXmlReport\n\n# Open HTML report\nopen build/reports/kover/html/index.html\n\n# Run specific test class\n./gradlew test --tests "com.example.UserServiceTest"\n\n# Run with verbose output\n./gradlew test --info\n```\n\n## Coverage Targets\n\n| Code Type | Target |\n|-----------|--------|\n| Critical business logic | 100% |\n| Public APIs | 90%+ |\n| General code | 80%+ |\n| Generated code | Exclude |\n\n## TDD Best Practices\n\n**DO:**\n- Write test FIRST, before any implementation\n- Run tests after each change\n- Use Kotest matchers for expressive assertions\n- Use MockK\'s `coEvery`/`coVerify` for suspend functions\n- Test behavior, not implementation details\n- Include edge cases (empty, null, max values)\n\n**DON\'T:**\n- Write implementation before tests\n- Skip the RED phase\n- Test private functions directly\n- Use `Thread.sleep()` in coroutine tests\n- Ignore flaky tests\n\n## Related Commands\n\n- `/kotlin-build` - Fix build errors\n- `/kotlin-review` - Review code after implementation\n- `verification-loop` skill - Run full verification loop\n\n## Related\n\n- Skill: `skills/kotlin-testing/`\n- Skill: `skills/tdd-workflow/`\n'
    ctx.register_command(
        name="kotlin-test",
        handler=_handle_kotlin_test,
        description="ECC /kotlin-test command",
    )


    # Register /gradle-build slash command
    def _handle_gradle_build(raw_args: str) -> str:
        return '---\ndescription: Fix Gradle build errors for Android and KMP projects\n---\n\n# Gradle Build Fix\n\nIncrementally fix Gradle build and compilation errors for Android and Kotlin Multiplatform projects.\n\n## Step 1: Detect Build Configuration\n\nIdentify the project type and run the appropriate build:\n\n| Indicator | Build Command |\n|-----------|---------------|\n| `build.gradle.kts` + `composeApp/` (KMP) | `./gradlew composeApp:compileKotlinMetadata 2>&1` |\n| `build.gradle.kts` + `app/` (Android) | `./gradlew app:compileDebugKotlin 2>&1` |\n| `settings.gradle.kts` with modules | `./gradlew assemble 2>&1` |\n| Detekt configured | `./gradlew detekt 2>&1` |\n\nAlso check `gradle.properties` and `local.properties` for configuration.\n\n## Step 2: Parse and Group Errors\n\n1. Run the build command and capture output\n2. Separate Kotlin compilation errors from Gradle configuration errors\n3. Group by module and file path\n4. Sort: configuration errors first, then compilation errors by dependency order\n\n## Step 3: Fix Loop\n\nFor each error:\n\n1. **Read the file** — Full context around the error line\n2. **Diagnose** — Common categories:\n   - Missing import or unresolved reference\n   - Type mismatch or incompatible types\n   - Missing dependency in `build.gradle.kts`\n   - Expect/actual mismatch (KMP)\n   - Compose compiler error\n3. **Fix minimally** — Smallest change that resolves the error\n4. **Re-run build** — Verify fix and check for new errors\n5. **Continue** — Move to next error\n\n## Step 4: Guardrails\n\nStop and ask the user if:\n- Fix introduces more errors than it resolves\n- Same error persists after 3 attempts\n- Error requires adding new dependencies or changing module structure\n- Gradle sync itself fails (configuration-phase error)\n- Error is in generated code (Room, SQLDelight, KSP)\n\n## Step 5: Summary\n\nReport:\n- Errors fixed (module, file, description)\n- Errors remaining\n- New errors introduced (should be zero)\n- Suggested next steps\n\n## Common Gradle/KMP Fixes\n\n| Error | Fix |\n|-------|-----|\n| Unresolved reference in `commonMain` | Check if the dependency is in `commonMain.dependencies {}` |\n| Expect declaration without actual | Add `actual` implementation in each platform source set |\n| Compose compiler version mismatch | Align Kotlin and Compose compiler versions in `libs.versions.toml` |\n| Duplicate class | Check for conflicting dependencies with `./gradlew dependencies` |\n| KSP error | Run `./gradlew kspCommonMainKotlinMetadata` to regenerate |\n| Configuration cache issue | Check for non-serializable task inputs |\n'
    ctx.register_command(
        name="gradle-build",
        handler=_handle_gradle_build,
        description="ECC /gradle-build command",
    )

