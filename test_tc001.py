import pytest
from playwright.sync_api import Page, expect

def test_successful_login(page: Page):
    # Step 1: Navigate to login page
    page.goto("https://freelance-learn-automation.vercel.app/login")
    expect(page).to_have_title("Learn Automation Courses")

    # Step 2: Enter valid email address
    email_input = page.get_by_placeholder("Enter Email")
    email_input.fill("admin@email.com")
    expect(email_input).to_have_value("admin@email.com")

    # Step 3: Enter valid password
    password_input = page.get_by_placeholder("Enter Password")
    password_input.fill("admin@123")
    expect(password_input).to_have_value("admin@123")

    # Step 4: Click the Sign in button
    sign_in_button = page.get_by_role("button", name="Sign in")
    sign_in_button.click()

    # Step 5: Verify URL should not be in url
    expect(page).not_to_have_url("*/login")