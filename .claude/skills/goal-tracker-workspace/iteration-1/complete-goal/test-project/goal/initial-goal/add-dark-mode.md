# Add Dark Mode to Dashboard

## Description
Add a dark mode toggle to the config dashboard with persistent preference storage.

## Steps
1. Add CSS variables for dark theme colors — Define light and dark color schemes using CSS custom properties
2. Create a toggle component — Build a sun/moon toggle button in the dashboard header
3. Wire up theme switching — Add JavaScript to toggle a data-theme attribute on the document root
4. Persist user preference — Save the choice to localStorage and restore on page load
5. Test across all pages — Verify all dashboard views look correct in both themes

## Success Criteria
- Toggle switches between light and dark themes instantly
- Preference survives page reloads
- All text is readable in both themes
- No flicker on page load

## Constraints
- Must work without a build step (vanilla JS + CSS)
- Should follow existing dashboard styling conventions
