package com.kidscheck.app.util

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class TokenManagerTest {

    private lateinit var context: Context

    @Before
    fun setup() {
        context = ApplicationProvider.getApplicationContext()
        // Clear any existing data
        TokenManager.clear(context)
    }

    @Test
    fun `getToken returns null when no token saved`() {
        assertNull(TokenManager.getToken(context))
    }

    @Test
    fun `saveToken and getToken`() {
        TokenManager.saveToken(context, "test_token", "baba", "parent", 1)
        assertEquals("test_token", TokenManager.getToken(context))
    }

    @Test
    fun `getUsername returns saved username`() {
        TokenManager.saveToken(context, "token", "mama", "parent", 2)
        assertEquals("mama", TokenManager.getUsername(context))
    }

    @Test
    fun `getRole returns saved role`() {
        TokenManager.saveToken(context, "token", "yeye", "grandparent", 3)
        assertEquals("grandparent", TokenManager.getRole(context))
    }

    @Test
    fun `getUserId returns saved userId`() {
        TokenManager.saveToken(context, "token", "baba", "parent", 42)
        assertEquals(42, TokenManager.getUserId(context))
    }

    @Test
    fun `getUserId returns -1 when no userId saved`() {
        assertEquals(-1, TokenManager.getUserId(context))
    }

    @Test
    fun `isLoggedIn returns false when no token`() {
        assertFalse(TokenManager.isLoggedIn(context))
    }

    @Test
    fun `isLoggedIn returns true when token exists`() {
        TokenManager.saveToken(context, "token", "baba", "parent", 1)
        assertTrue(TokenManager.isLoggedIn(context))
    }

    @Test
    fun `clear removes all data`() {
        TokenManager.saveToken(context, "token", "baba", "parent", 1)
        TokenManager.clear(context)

        assertNull(TokenManager.getToken(context))
        assertNull(TokenManager.getUsername(context))
        assertNull(TokenManager.getRole(context))
        assertEquals(-1, TokenManager.getUserId(context))
        assertFalse(TokenManager.isLoggedIn(context))
    }

    @Test
    fun `saveToken overwrites previous token`() {
        TokenManager.saveToken(context, "old_token", "baba", "parent", 1)
        TokenManager.saveToken(context, "new_token", "mama", "parent", 2)

        assertEquals("new_token", TokenManager.getToken(context))
        assertEquals("mama", TokenManager.getUsername(context))
        assertEquals(2, TokenManager.getUserId(context))
    }

    @Test
    fun `getUsername returns null when no username saved`() {
        assertNull(TokenManager.getUsername(context))
    }

    @Test
    fun `getRole returns null when no role saved`() {
        assertNull(TokenManager.getRole(context))
    }
}
