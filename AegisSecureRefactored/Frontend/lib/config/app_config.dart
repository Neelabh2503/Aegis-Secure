class AppConfig {
  AppConfig._();

  static const String baseUrl = "https://AEGIS14211-AegisSecureBackend.hf.space";
  static const String cyberApiUrl = "https://akshatbhatt515334-aegis-secure-api.hf.space/predict";
  
  static const String googleClientId = "365011130597-3bv38b9aubtt65rebnbl673c2cogt7j3.apps.googleusercontent.com";
  static const String googleRedirectUri = "$baseUrl/auth/google/callback";
  static const String googleAuthScope = "https://www.googleapis.com/auth/gmail.readonly";
  
  static const String authLoginEndpoint = "$baseUrl/auth/login";
  static const String authRegisterEndpoint = "$baseUrl/auth/register";
  static const String authMeEndpoint = "$baseUrl/auth/me";
  static const String authSendOtpEndpoint = "$baseUrl/auth/send-otp";
  static const String authVerifyOtpEndpoint = "$baseUrl/auth/verify-otp";
  static const String authResetPasswordEndpoint = "$baseUrl/auth/reset-password";
  static const String authCheckEmailEndpoint = "$baseUrl/auth/check-email";
  static const String authGoogleCallbackEndpoint = "$baseUrl/auth/google/callback";
  
  static const String gmailAccountsEndpoint = "$baseUrl/gmail/accounts";
  static const String gmailRefreshEndpoint = "$baseUrl/gmail/refresh";
  static const String gmailStateTokenEndpoint = "$baseUrl/gmail/state-token";
  
  static const String emailsEndpoint = "$baseUrl/emails";
  static const String emailsSearchEndpoint = "$baseUrl/emails/search";
  
  static const String smsAllEndpoint = "$baseUrl/sms/all";
  static const String smsSyncEndpoint = "$baseUrl/sms/sync";
  static const String smsAnalyzeListEndpoint = "$baseUrl/analyze_sms_list";
  
  static const String dashboardEndpoint = "$baseUrl/dashboard";
  
  static const String accountsDeleteEndpoint = "$baseUrl/accounts/delete";
  static const String accountAvatarEndpoint = "$baseUrl/auth/me/avatar";
  
  static const int initialSmsFetchLimit = 10;
  static const int smsDeviceLimit = 2;
  static const int smsSyncLimit = 25;
  
  static const String jwtTokenKey = 'jwt_token';
  static const String savedAccountsKey = 'saved_accounts';
  static const String activeLinkedEmailKey = 'active_linked_email';
  static const String selectedGmailAccountKey = 'selectedGmailAccount';
  static const String autoFetchSmsKey = 'auto_fetch_sms_enabled';
  
  static const String contentTypeJson = 'application/json';
  static const String ngrokSkipBrowserWarning = 'true';
}
