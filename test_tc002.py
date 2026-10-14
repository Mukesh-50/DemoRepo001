from playwright.sync_api import Page, expect

def test_login_fails_with_invalid_password(page: Page):
    # Step 1: Navigate to login page
    page.goto("https://freelance-learn-automation.vercel.app/login")
    expect(page).to_have_url("https://freelance-learn-automation.vercel.app/login")

    # Step 2: Enter valid email address
    page.get_by_placeholder("Enter Email").fill("admin@email.com")
    expect(page.get_by_placeholder("Enter Email")).to_have_value("admin@email.com")

    # Step 3: Enter invalid password
    page.get_by_placeholder("Enter Password").fill("wrong@123")
    expect(page.get_by_placeholder("Enter Password")).to_have_value("wrong@123")

    # Step 4: Click the Sign in button
    page.get_by_role("button", name="Sign in").click()

    # Step 5: Verify user is still on login
    expect(page).to_have_url("https://freelance-learn-automation.vercel.app/login")