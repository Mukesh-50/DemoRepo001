import { test, expect } from '@playwright/test';

test('Verify Login Fails with Invalid Password', async ({ page }) => {
    await page.goto('https://freelance-learn-automation.vercel.app/login');
    await expect(page).toHaveURL(/.*login/);
    
    await page.getByPlaceholder('Enter Email').fill('admin@email.com');
    await expect(page.getByPlaceholder('Enter Email')).toHaveValue('admin@email.com');
    
    await page.getByPlaceholder('Enter Password').fill('wrong@123');
    await expect(page.getByPlaceholder('Enter Password')).toHaveValue('wrong@123');
    
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL(/.*login/);
});