import pytest
from playwright.sync_api import Page, expect

def test_new_user_signup_link(page: Page):
    # Step 1: Navigate to login page
    page.goto("https://freelance-learn-automation.vercel.app/login")
    expect(page).to_have_title("Learn Automation Courses")
    
    # Step 2: Click the "New user? Signup" link
    signup_link = page.get_by_role("link", name="New user? Signup")
    signup_link.click()
    
    # Step 3: Verify signup page URL
    expect(page).to_have_url("https://freelance-learn-automation.vercel.app/signup")