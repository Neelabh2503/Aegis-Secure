import 'package:flutter/material.dart';
import '../config/app_constants.dart';

class DateFormatter {
  DateFormatter._();

  /// Format date as short month and day (e.g., "Jan 15")
  static String formatShortDate(DateTime date) {
    return "${AppConstants.monthNames[date.month - 1]} ${date.day}";
  }

  /// Format time as HH:MM for today, or DD/MM for other days
  static String formatTime(DateTime dt) {
    final now = DateTime.now();
    if (now.difference(dt).inDays == 0) {
      return "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
    } else {
      return "${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}";
    }
  }

  /// Format date as full string (e.g., "January 15, 2024")
  static String formatFullDate(DateTime date) {
    const fullMonths = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    return "${fullMonths[date.month - 1]} ${date.day}, ${date.year}";
  }

  /// Format date as ISO string
  static String formatISODate(DateTime date) {
    return date.toIso8601String();
  }

  /// Parse milliseconds to DateTime
  static DateTime fromMilliseconds(int milliseconds) {
    return DateTime.fromMillisecondsSinceEpoch(milliseconds, isUtc: true).toLocal();
  }

  /// Get relative time string (e.g., "2 hours ago", "3 days ago")
  static String getRelativeTime(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays > 365) {
      final years = (difference.inDays / 365).floor();
      return years == 1 ? '1 year ago' : '$years years ago';
    } else if (difference.inDays > 30) {
      final months = (difference.inDays / 30).floor();
      return months == 1 ? '1 month ago' : '$months months ago';
    } else if (difference.inDays > 0) {
      return difference.inDays == 1 ? '1 day ago' : '${difference.inDays} days ago';
    } else if (difference.inHours > 0) {
      return difference.inHours == 1 ? '1 hour ago' : '${difference.inHours} hours ago';
    } else if (difference.inMinutes > 0) {
      return difference.inMinutes == 1 ? '1 minute ago' : '${difference.inMinutes} minutes ago';
    } else {
      return 'Just now';
    }
  }
}
