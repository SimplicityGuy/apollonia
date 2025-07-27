"""End-to-end tests for the Apollonia frontend using Playwright."""

import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Page, expect


class TestFrontendE2E:
    """End-to-end tests for the frontend application."""

    @pytest.fixture
    def base_url(self) -> str:
        """Get the base URL for the frontend."""
        return os.getenv("FRONTEND_URL", "http://localhost:3000")

    @pytest.fixture
    def api_url(self) -> str:
        """Get the API URL."""
        return os.getenv("API_URL", "http://localhost:8000")

    @pytest.fixture(autouse=True)
    def setup_teardown(self, page: Page) -> Iterator[None]:
        """Setup and teardown for each test."""
        # Clear local storage before each test
        page.goto("http://localhost:3000")
        page.evaluate("() => localStorage.clear()")
        yield
        # Cleanup after test if needed

    def test_homepage_loads(self, page: Page, base_url: str) -> None:
        """Test that the homepage loads successfully."""
        page.goto(base_url)

        # Check page title
        expect(page).to_have_title("Apollonia")

        # Check main heading
        expect(page.locator("h1")).to_contain_text("Dashboard")

        # Check statistics cards are visible
        expect(page.locator("text=Total Media Files")).to_be_visible()
        expect(page.locator("text=Analyzed Files")).to_be_visible()
        expect(page.locator("text=Processing Queue")).to_be_visible()
        expect(page.locator("text=Storage Used")).to_be_visible()

    def test_navigation_menu(self, page: Page, base_url: str) -> None:
        """Test navigation menu functionality."""
        page.goto(base_url)

        # Check sidebar navigation items
        expect(page.locator("text=Dashboard")).to_be_visible()
        expect(page.locator("text=Catalogs")).to_be_visible()
        expect(page.locator("text=Upload")).to_be_visible()
        expect(page.locator("text=Analytics")).to_be_visible()
        expect(page.locator("text=Settings")).to_be_visible()

        # Click on Catalogs
        page.click("text=Catalogs")
        expect(page).to_have_url(f"{base_url}/catalogs")

        # Click on Upload
        page.click("text=Upload")
        expect(page).to_have_url(f"{base_url}/upload")

    def test_search_functionality(self, page: Page, base_url: str) -> None:
        """Test search bar functionality."""
        page.goto(base_url)

        # Find search input
        search_input = page.locator('input[type="search"]')
        expect(search_input).to_be_visible()
        expect(search_input).to_have_attribute("placeholder", "Search media files...")

        # Type in search
        search_input.fill("test video")
        search_input.press("Enter")

        # Should navigate to search page
        expect(page).to_have_url(f"{base_url}/search?q=test+video")

    def test_user_authentication_flow(self, page: Page, base_url: str) -> None:
        """Test user login and logout flow."""
        # Go to login page
        page.goto(f"{base_url}/login")

        # Check login form
        expect(page.locator("h2")).to_contain_text("Sign in to your account")
        expect(page.locator('label:has-text("Username")')).to_be_visible()
        expect(page.locator('label:has-text("Password")')).to_be_visible()

        # Fill login form
        page.fill('input[name="username"]', "testuser")
        page.fill('input[name="password"]', "testpass123")

        # Mock successful login response
        page.route(
            "**/api/auth/login",
            lambda route: route.fulfill(
                status=200, json={"token": "fake-jwt-token", "user": {"username": "testuser"}}
            ),
        )

        # Submit form
        page.click('button:has-text("Sign in")')

        # Should redirect to dashboard
        expect(page).to_have_url(base_url + "/")

        # Check user menu is visible
        expect(page.locator('button[aria-label="Open user menu"]')).to_be_visible()

        # Open user menu
        page.click('button[aria-label="Open user menu"]')

        # Check menu items
        expect(page.locator("text=Settings")).to_be_visible()
        expect(page.locator("text=Sign out")).to_be_visible()

        # Click sign out
        page.click("text=Sign out")

        # Should redirect to login
        expect(page).to_have_url(f"{base_url}/login")

    def test_file_upload_page(self, page: Page, base_url: str) -> None:
        """Test file upload functionality."""
        page.goto(f"{base_url}/upload")

        # Check upload page elements
        expect(page.locator("h1")).to_contain_text("Upload")

        # Check for file input
        file_input = page.locator('input[type="file"]')
        expect(file_input).to_be_attached()

        # Upload a test file
        test_file = Path(__file__).parent / "test_file.txt"
        test_file.write_text("Test content")

        file_input.set_input_files(str(test_file))

        # Mock upload response
        page.route(
            "**/api/upload",
            lambda route: route.fulfill(
                status=200, json={"id": "123", "filename": "test_file.txt", "status": "uploaded"}
            ),
        )

        # Click upload button
        page.click('button:has-text("Upload")')

        # Check for success message
        expect(page.locator("text=Upload successful")).to_be_visible(timeout=5000)

        # Cleanup
        test_file.unlink()

    def test_recent_files_table(self, page: Page, base_url: str) -> None:
        """Test recent files table on homepage."""
        # Mock API response for recent files
        page.route(
            "**/api/media/files*",
            lambda route: route.fulfill(
                status=200,
                json={
                    "items": [
                        {
                            "id": "1",
                            "filename": "video1.mp4",
                            "media_type": "video/mp4",
                            "file_size": 1048576,
                            "processing_status": "completed",
                            "created_at": "2024-01-01T00:00:00Z",
                        },
                        {
                            "id": "2",
                            "filename": "image1.jpg",
                            "media_type": "image/jpeg",
                            "file_size": 524288,
                            "processing_status": "processing",
                            "created_at": "2024-01-02T00:00:00Z",
                        },
                    ],
                    "total": 2,
                    "page": 1,
                    "page_size": 10,
                },
            ),
        )

        page.goto(base_url)

        # Wait for table to load
        expect(page.locator("text=Recent Files")).to_be_visible()

        # Check table headers
        expect(page.locator("th:has-text('Name')")).to_be_visible()
        expect(page.locator("th:has-text('Type')")).to_be_visible()
        expect(page.locator("th:has-text('Size')")).to_be_visible()
        expect(page.locator("th:has-text('Status')")).to_be_visible()

        # Check file entries
        expect(page.locator("text=video1.mp4")).to_be_visible()
        expect(page.locator("text=image1.jpg")).to_be_visible()

        # Check status badges
        expect(page.locator(".bg-green-100:has-text('completed')")).to_be_visible()
        expect(page.locator(".bg-yellow-100:has-text('processing')")).to_be_visible()

        # Click on view link
        page.click("a:has-text('View'):first")
        expect(page).to_have_url(f"{base_url}/files/1")

    def test_responsive_design(self, page: Page, base_url: str) -> None:
        """Test responsive design on different viewport sizes."""
        page.goto(base_url)

        # Desktop view
        page.set_viewport_size({"width": 1920, "height": 1080})
        expect(page.locator(".lg\\:fixed")).to_be_visible()  # Desktop sidebar

        # Mobile view
        page.set_viewport_size({"width": 375, "height": 667})
        expect(page.locator(".lg\\:hidden")).to_be_visible()  # Mobile menu button

        # Click mobile menu button
        page.click('button[aria-label="Open sidebar"]')

        # Mobile sidebar should be visible
        expect(page.locator(".lg\\:hidden .relative.z-40")).to_be_visible()

    def test_dark_mode_toggle(self, page: Page, base_url: str) -> None:
        """Test dark mode toggle functionality."""
        page.goto(f"{base_url}/settings")

        # Look for dark mode toggle
        dark_mode_toggle = page.locator('button:has-text("Dark Mode")')

        if dark_mode_toggle.is_visible():
            # Toggle dark mode
            dark_mode_toggle.click()

            # Check that dark class is applied to html
            expect(page.locator("html")).to_have_class(re.compile(r"dark"))

            # Toggle back
            dark_mode_toggle.click()
            expect(page.locator("html")).not_to_have_class(re.compile(r"dark"))

    def test_error_handling(self, page: Page, base_url: str) -> None:
        """Test error handling and error pages."""
        # Navigate to non-existent page
        page.goto(f"{base_url}/non-existent-page")

        # Should show 404 page
        expect(page.locator("text=404")).to_be_visible()
        expect(page.locator("text=Page not found")).to_be_visible()

        # Mock API error
        page.route(
            "**/api/media/files*",
            lambda route: route.fulfill(status=500, json={"error": "Internal Server Error"}),
        )

        page.goto(base_url)

        # Should handle error gracefully
        # (Exact behavior depends on error handling implementation)

    def test_catalog_page_functionality(self, page: Page, base_url: str) -> None:
        """Test catalog listing and interaction."""
        # Mock catalog API response
        page.route(
            "**/api/catalogs*",
            lambda route: route.fulfill(
                status=200,
                json={
                    "items": [
                        {
                            "id": "1",
                            "name": "Movies",
                            "description": "Movie collection",
                            "item_count": 150,
                            "created_at": "2024-01-01T00:00:00Z",
                        },
                        {
                            "id": "2",
                            "name": "Music",
                            "description": "Music collection",
                            "item_count": 500,
                            "created_at": "2024-01-02T00:00:00Z",
                        },
                    ],
                    "total": 2,
                },
            ),
        )

        page.goto(f"{base_url}/catalogs")

        # Check catalog cards
        expect(page.locator("text=Movies")).to_be_visible()
        expect(page.locator("text=Music")).to_be_visible()
        expect(page.locator("text=150 items")).to_be_visible()
        expect(page.locator("text=500 items")).to_be_visible()

        # Click on a catalog
        page.click("text=Movies")
        expect(page).to_have_url(f"{base_url}/catalogs/1")

    def test_keyboard_navigation(self, page: Page, base_url: str) -> None:
        """Test keyboard navigation and accessibility."""
        page.goto(base_url)

        # Tab through interactive elements
        page.keyboard.press("Tab")

        # Check focus is visible
        focused = page.locator(":focus")
        expect(focused).to_be_visible()

        # Press Enter on focused link
        page.keyboard.press("Enter")

        # Should navigate based on focused element

    def test_loading_states(self, page: Page, base_url: str) -> None:
        """Test loading states for async operations."""

        # Delay API response to see loading state
        def delayed_route(route: Any) -> None:
            page.wait_for_timeout(2000)  # This returns None but we don't need the return value
            route.fulfill(status=200, json={"items": [], "total": 0})

        page.route("**/api/media/files*", delayed_route)

        page.goto(base_url)

        # Check for loading indicators
        # (Exact selectors depend on implementation)
        loading_indicator = page.locator(".animate-spin, .loading, [aria-busy='true']")
        if loading_indicator.is_visible():
            expect(loading_indicator).to_be_visible()
            # Wait for loading to complete
            expect(loading_indicator).not_to_be_visible(timeout=5000)
