package com.kidscheck.app.util

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import java.io.ByteArrayOutputStream
import java.io.File

object PhotoCompressor {
    private const val MAX_SIZE_BYTES = 1024 * 1024 // 1MB
    private const val MAX_DIMENSION = 1920

    fun compressPhoto(context: Context, uri: Uri): ByteArray {
        val inputStream = context.contentResolver.openInputStream(uri)
        val originalBitmap = BitmapFactory.decodeStream(inputStream)
        inputStream?.close()

        val scaled = scaleDown(originalBitmap)
        var quality = 85
        var bytes = toByteArray(scaled, quality)

        while (bytes.size > MAX_SIZE_BYTES && quality > 10) {
            quality -= 10
            bytes = toByteArray(scaled, quality)
        }

        if (scaled !== originalBitmap) scaled.recycle()
        originalBitmap.recycle()

        return bytes
    }

    fun compressFile(file: File): ByteArray {
        val originalBitmap = BitmapFactory.decodeFile(file.absolutePath)
            ?: return file.readBytes()

        val scaled = scaleDown(originalBitmap)
        var quality = 85
        var bytes = toByteArray(scaled, quality)

        while (bytes.size > MAX_SIZE_BYTES && quality > 10) {
            quality -= 10
            bytes = toByteArray(scaled, quality)
        }

        if (scaled !== originalBitmap) scaled.recycle()
        originalBitmap.recycle()

        return bytes
    }

    private fun scaleDown(bitmap: Bitmap): Bitmap {
        val w = bitmap.width
        val h = bitmap.height
        if (w <= MAX_DIMENSION && h <= MAX_DIMENSION) return bitmap
        val ratio = MAX_DIMENSION.toFloat() / maxOf(w, h)
        return Bitmap.createScaledBitmap(bitmap, (w * ratio).toInt(), (h * ratio).toInt(), true)
    }

    private fun toByteArray(bitmap: Bitmap, quality: Int): ByteArray {
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, quality, stream)
        return stream.toByteArray()
    }
}
