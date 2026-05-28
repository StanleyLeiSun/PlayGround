package com.kidscheck.app.testutil

import android.util.Log
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.RecordedRequest

class MockApiDispatcher : Dispatcher() {

    private data class ResponseEntry(
        val method: String,
        val pathPattern: Regex,
        val body: String,
        val code: Int = 200,
        val delayMs: Long = 0
    )

    private val responses = mutableListOf<ResponseEntry>()

    fun register(method: String, path: String, body: String, code: Int = 200, delayMs: Long = 0) {
        // Convert path patterns to regex:
        // - /api/auth/login -> ^/api/auth/login$ (exact match)
        // - /api/daily-tasks/.* -> ^/api/daily-tasks/.*$ (already regex)
        // - /api/templates/{childId} -> ^/api/templates/[^/]+$ (parameterized)
        val regexStr = buildString {
            append("^")
            var i = 0
            while (i < path.length) {
                if (path[i] == '{') {
                    // Parameter placeholder - match any non-slash segment
                    val end = path.indexOf('}', i)
                    if (end > i) {
                        append("[^/]+")
                        i = end + 1
                    } else {
                        append(Regex.escape(path[i].toString()))
                        i++
                    }
                } else if (path[i] == '.' && i + 1 < path.length && path[i + 1] == '*') {
                    // .* wildcard - keep as regex
                    append(".*")
                    i += 2
                } else {
                    // Literal character - escape for regex
                    append(Regex.escape(path[i].toString()))
                    i++
                }
            }
            append("$")
        }
        responses.add(ResponseEntry(method.uppercase(), Regex(regexStr), body, code, delayMs))
    }

    fun registerExact(method: String, path: String, body: String, code: Int = 200) {
        responses.add(ResponseEntry(method.uppercase(), Regex("^${Regex.escape(path)}$"), body, code))
    }

    fun clear() {
        responses.clear()
    }

    override fun dispatch(request: RecordedRequest): MockResponse {
        val method = request.method?.uppercase() ?: "GET"
        val path = request.path?.split("?")?.firstOrNull() ?: "/"
        Log.e("MockApiDispatcher", "Request: $method $path (registered: ${responses.size} entries)")

        for (entry in responses.reversed()) {
            if (entry.method == method && entry.pathPattern.matches(path)) {
                Log.e("MockApiDispatcher", "  MATCHED: ${entry.method} ${entry.pathPattern.pattern} -> ${entry.code}")
                val response = MockResponse()
                    .setResponseCode(entry.code)
                    .setHeader("Content-Type", "application/json")
                    .setBody(entry.body)
                if (entry.delayMs > 0) {
                    response.setBodyDelay(entry.delayMs, java.util.concurrent.TimeUnit.MILLISECONDS)
                }
                return response
            }
        }

        // Default: return 404 for unmatched requests
        Log.e("MockApiDispatcher", "  NO MATCH for $method $path (entries: ${responses.map { "${it.method} ${it.pathPattern.pattern}" }})")
        return MockResponse()
            .setResponseCode(404)
            .setHeader("Content-Type", "application/json")
            .setBody("""{"detail": "Not found: $method $path"}""")
    }
}
