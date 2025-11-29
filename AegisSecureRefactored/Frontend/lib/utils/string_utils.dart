class StringUtils {
  StringUtils._();

  static bool isValidEmail(String email) {
    final emailRegex = RegExp(
      r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    );
    return emailRegex.hasMatch(email);
  }

  static bool isNullOrEmpty(String? value) {
    return value == null || value.trim().isEmpty();
  }

  static String getInitials(String name) {
    if (name.isEmpty) return '?';
    
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.length == 1) {
      return parts[0][0].toUpperCase();
    } else {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
  }

  static String truncate(String text, int maxLength, {String ellipsis = '...'}) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - ellipsis.length) + ellipsis;
  }

  static String capitalize(String text) {
    if (text.isEmpty) return text;
    return text[0].toUpperCase() + text.substring(1).toLowerCase();
  }

  static bool isNumeric(String text) {
    return RegExp(r'^\d+$').hasMatch(text);
  }

  static String removeWhitespace(String text) {
    return text.replaceAll(RegExp(r'\s+'), '');
  }

  static String formatPhoneNumber(String phone) {
    final cleaned = removeWhitespace(phone);
    if (cleaned.length == 10) {
      return '(${cleaned.substring(0, 3)}) ${cleaned.substring(3, 6)}-${cleaned.substring(6)}';
    }
    return phone;
  }

  static bool isBusinessSender(String address) {
    return RegExp(r'[A-Za-z]').hasMatch(address);
  }

  static String formatBusinessSender(String address) {
    return address.replaceAll(RegExp(r'^[A-Z]{2}-'), '');
  }

  static String getDisplayName(String address, String? contactName) {
    if (contactName != null && contactName.isNotEmpty) {
      return contactName;
    }
    
    if (isBusinessSender(address)) {
      return formatBusinessSender(address);
    }
    
    return address;
  }
}
