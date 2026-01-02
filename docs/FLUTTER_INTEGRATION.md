# Bariq Al-Yusr - Flutter Mobile App Integration Guide

This document provides instructions for integrating the Flutter mobile app with the Bariq backend API, including authentication, push notifications, payments, and real-time updates.

## Base Configuration

```dart
class ApiConfig {
  // Development
  static const String baseUrl = 'http://localhost:5001/api/v1';

  // Production (update with your actual domain)
  // static const String baseUrl = 'https://api.bariq.sa/api/v1';
}
```

## Authentication

### Customer Login via Nafath (Saudi SSO)

```dart
// 1. Initiate Nafath authentication
Future<NafathResponse> initiateNafath(String nationalId) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/customer/nafath/initiate'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'national_id': nationalId}),
  );

  return NafathResponse.fromJson(jsonDecode(response.body));
}

// Response contains transId and random code for user to verify in Nafath app

// 2. Verify Nafath callback
Future<AuthResponse> verifyNafath(String transId) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/customer/nafath/callback'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'trans_id': transId}),
  );

  return AuthResponse.fromJson(jsonDecode(response.body));
}
```

### Customer Login with Bariq ID

```dart
Future<AuthResponse> loginWithBariqId(String bariqId, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/customer/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'bariq_id': bariqId,
      'password': password,
    }),
  );

  final data = jsonDecode(response.body);
  if (data['success']) {
    // Store tokens securely
    await secureStorage.write(key: 'access_token', value: data['data']['access_token']);
    await secureStorage.write(key: 'refresh_token', value: data['data']['refresh_token']);
  }

  return AuthResponse.fromJson(data);
}
```

### Token Refresh

```dart
Future<void> refreshToken() async {
  final refreshToken = await secureStorage.read(key: 'refresh_token');

  final response = await http.post(
    Uri.parse('$baseUrl/auth/customer/refresh'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $refreshToken',
    },
  );

  final data = jsonDecode(response.body);
  if (data['success']) {
    await secureStorage.write(key: 'access_token', value: data['data']['access_token']);
  }
}
```

### Merchant Staff Login

```dart
Future<AuthResponse> merchantLogin(String email, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/merchant/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
    }),
  );

  return AuthResponse.fromJson(jsonDecode(response.body));
}
```

## Push Notifications (Firebase FCM)

### Setup Firebase in Flutter

1. Add dependencies to `pubspec.yaml`:
```yaml
dependencies:
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
```

2. Initialize Firebase and register device:

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

class PushNotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;

  Future<void> initialize() async {
    // Request permission (iOS)
    await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // Get FCM token
    String? token = await _fcm.getToken();
    if (token != null) {
      await registerDevice(token);
    }

    // Listen for token refresh
    _fcm.onTokenRefresh.listen((newToken) {
      registerDevice(newToken);
    });

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_handleBackgroundMessage);

    // Handle notification tap
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
  }

  void _handleForegroundMessage(RemoteMessage message) {
    // Show local notification or update UI
    print('Foreground message: ${message.notification?.title}');
  }

  void _handleNotificationTap(RemoteMessage message) {
    // Navigate based on notification type
    final data = message.data;
    switch (data['notification_type']) {
      case 'transaction_pending':
        // Navigate to transaction details
        navigateTo('/transactions/${data['entity_id']}');
        break;
      case 'payment_success':
        navigateTo('/payments/${data['entity_id']}');
        break;
      // Add more cases as needed
    }
  }
}

@pragma('vm:entry-point')
Future<void> _handleBackgroundMessage(RemoteMessage message) async {
  // Handle background message
  print('Background message: ${message.notification?.title}');
}
```

### Register Device with Backend

```dart
// For Customer App
Future<void> registerDevice(String fcmToken) async {
  final accessToken = await secureStorage.read(key: 'access_token');

  await http.post(
    Uri.parse('$baseUrl/customers/me/devices'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    },
    body: jsonEncode({
      'fcm_token': fcmToken,
      'device_type': Platform.isIOS ? 'ios' : 'android',
      'device_name': await getDeviceName(),  // e.g., "iPhone 14 Pro"
      'device_id': await getDeviceId(),       // unique device identifier
    }),
  );
}

// For Merchant App
Future<void> registerMerchantDevice(String fcmToken) async {
  final accessToken = await secureStorage.read(key: 'access_token');

  await http.post(
    Uri.parse('$baseUrl/merchants/me/devices'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    },
    body: jsonEncode({
      'fcm_token': fcmToken,
      'device_type': Platform.isIOS ? 'ios' : 'android',
      'device_name': await getDeviceName(),
      'device_id': await getDeviceId(),
    }),
  );
}
```

### Unregister Device on Logout

```dart
Future<void> logout() async {
  final accessToken = await secureStorage.read(key: 'access_token');

  // Get device ID from storage
  final deviceId = await secureStorage.read(key: 'device_id');

  if (deviceId != null) {
    await http.delete(
      Uri.parse('$baseUrl/customers/me/devices/$deviceId'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
  }

  // Clear tokens
  await secureStorage.deleteAll();
}
```

## Payment Integration (PayTabs)

### Initiate Payment

```dart
Future<PaymentResponse> initiatePayment({
  required List<String> transactionIds,
  required double amount,
  String paymentMethod = 'all',
}) async {
  final accessToken = await secureStorage.read(key: 'access_token');

  final response = await http.post(
    Uri.parse('$baseUrl/customers/me/payments/initiate'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    },
    body: jsonEncode({
      'transaction_ids': transactionIds,
      'amount': amount,
      'payment_method': paymentMethod,  // 'all', 'creditcard', 'mada', 'stcpay', 'applepay'
    }),
  );

  return PaymentResponse.fromJson(jsonDecode(response.body));
}
```

### Open Payment in WebView

```dart
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

class PaymentWebView extends StatefulWidget {
  final String paymentUrl;
  final String paymentId;

  const PaymentWebView({
    required this.paymentUrl,
    required this.paymentId,
  });

  @override
  _PaymentWebViewState createState() => _PaymentWebViewState();
}

class _PaymentWebViewState extends State<PaymentWebView> {
  late InAppWebViewController _controller;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('الدفع')),
      body: InAppWebView(
        initialUrlRequest: URLRequest(url: Uri.parse(widget.paymentUrl)),
        onWebViewCreated: (controller) {
          _controller = controller;

          // Add JavaScript handler for payment completion
          controller.addJavaScriptHandler(
            handlerName: 'paymentComplete',
            callback: (args) {
              final message = args[0] as Map<String, dynamic>;
              _handlePaymentComplete(message);
            },
          );
        },
        onLoadStop: (controller, url) async {
          // Check if we're on the completion page
          final currentUrl = url.toString();
          if (currentUrl.contains('/payment/complete')) {
            // Payment process finished - callback will handle the rest
          }
        },
      ),
    );
  }

  void _handlePaymentComplete(Map<String, dynamic> message) {
    final success = message['success'] as bool;
    final tranRef = message['tranRef'] as String?;

    Navigator.of(context).pop({
      'success': success,
      'tranRef': tranRef,
      'status': message['status'],
    });
  }
}
```

### Check Payment Status

```dart
Future<PaymentStatus> checkPaymentStatus(String paymentId) async {
  final accessToken = await secureStorage.read(key: 'access_token');

  final response = await http.get(
    Uri.parse('$baseUrl/customers/me/payments/$paymentId/status'),
    headers: {'Authorization': 'Bearer $accessToken'},
  );

  return PaymentStatus.fromJson(jsonDecode(response.body));
}

// Query PayTabs directly for real-time status
Future<PaymentStatus> queryPaymentGateway(String tranRef) async {
  final accessToken = await secureStorage.read(key: 'access_token');

  final response = await http.get(
    Uri.parse('$baseUrl/customers/me/payments/query/$tranRef'),
    headers: {'Authorization': 'Bearer $accessToken'},
  );

  return PaymentStatus.fromJson(jsonDecode(response.body));
}
```

### Get Available Payment Methods

```dart
Future<List<PaymentMethod>> getPaymentMethods() async {
  final accessToken = await secureStorage.read(key: 'access_token');

  final response = await http.get(
    Uri.parse('$baseUrl/customers/me/payment-methods'),
    headers: {'Authorization': 'Bearer $accessToken'},
  );

  final data = jsonDecode(response.body);
  return (data['data']['methods'] as List)
      .map((m) => PaymentMethod.fromJson(m))
      .toList();
}
```

## Customer API Endpoints

### Profile

```dart
// Get profile
GET /customers/me

// Update profile
PUT /customers/me
{
  "phone": "0501234567",
  "email": "user@example.com",
  "city": "Riyadh"
}

// Change password
PUT /customers/me/password
{
  "current_password": "old123",
  "new_password": "new123"
}
```

### Credit

```dart
// Get credit details
GET /customers/me/credit
// Response:
{
  "credit_limit": 5000,
  "used_credit": 1500,
  "available_credit": 3500
}

// Get credit health score
GET /customers/me/credit/health

// Request credit increase
POST /customers/me/credit/request-increase
{
  "requested_amount": 7000,
  "reason": "Increased shopping needs"
}
```

### Transactions

```dart
// Get transactions
GET /customers/me/transactions?status=active&page=1&per_page=20

// Get transaction details
GET /customers/me/transactions/{id}

// Confirm pending transaction
POST /customers/me/transactions/{id}/confirm

// Reject pending transaction
POST /customers/me/transactions/{id}/reject
{
  "reason": "I didn't make this purchase"
}
```

### Debt & Payments

```dart
// Get debt summary
GET /customers/me/debt
// Response:
{
  "total_debt": 1500,
  "overdue_amount": 0,
  "next_due_date": "2026-01-15",
  "transactions": [...]
}

// Get payment history
GET /customers/me/payments?page=1&per_page=20

// Make payment (alternative to PayTabs - for testing)
POST /customers/me/payments
{
  "transaction_ids": ["tx1", "tx2"],
  "amount": 500,
  "payment_method": "card"
}
```

### Notifications

```dart
// Get notifications
GET /customers/me/notifications?unread_only=true&page=1

// Mark as read
PUT /customers/me/notifications/{id}/read

// Mark all as read
POST /customers/me/notifications/read-all
```

### Devices

```dart
// Get registered devices
GET /customers/me/devices

// Register device
POST /customers/me/devices
{
  "fcm_token": "...",
  "device_type": "ios",  // or "android"
  "device_name": "iPhone 14 Pro",
  "device_id": "unique-device-id"
}

// Unregister device
DELETE /customers/me/devices/{device_id}
```

## Merchant API Endpoints

### Profile & Settings

```dart
GET /merchants/me           // Get merchant profile
PUT /merchants/me           // Update profile
```

### Transactions

```dart
// Create new transaction
POST /merchants/me/transactions
{
  "customer_bariq_id": "123456",
  "amount": 500,
  "description": "Electronics purchase"
}

// Get transactions
GET /merchants/me/transactions?status=pending&page=1

// Get transaction details
GET /merchants/me/transactions/{id}

// Cancel transaction
POST /merchants/me/transactions/{id}/cancel
```

### Staff Management (Admin/Manager only)

```dart
// Get staff list
GET /merchants/me/staff

// Create staff
POST /merchants/me/staff
{
  "name_ar": "احمد محمد",
  "email": "staff@merchant.com",
  "phone": "0501234567",
  "role": "cashier",  // cashier, supervisor, branch_manager, regional_manager
  "branch_id": "branch-uuid"
}

// Update staff
PUT /merchants/me/staff/{id}

// Deactivate staff
DELETE /merchants/me/staff/{id}
```

### Branches

```dart
GET /merchants/me/branches
POST /merchants/me/branches
GET /merchants/me/branches/{id}
PUT /merchants/me/branches/{id}
```

### Reports

```dart
GET /merchants/me/reports/summary?period=month
GET /merchants/me/reports/transactions?from=2026-01-01&to=2026-01-31
GET /merchants/me/settlements
```

### Notifications & Devices

```dart
GET /merchants/me/notifications
PUT /merchants/me/notifications/{id}/read
POST /merchants/me/notifications/read-all
GET /merchants/me/devices
POST /merchants/me/devices
DELETE /merchants/me/devices/{id}
```

## Error Handling

All API responses follow this format:

```dart
class ApiResponse<T> {
  final bool success;
  final String? message;
  final String? errorCode;
  final T? data;
  final Map<String, dynamic>? meta;  // pagination info
}
```

Common error codes:
- `VAL_001` - Validation error
- `AUTH_001` - Authentication failed
- `AUTH_002` - Token expired
- `AUTH_003` - Insufficient permissions
- `TRANS_001` - Transaction not found
- `PAY_001` - Payment failed
- `SYS_001` - System error

### HTTP Interceptor

```dart
class ApiInterceptor {
  Future<http.Response> request(
    String method,
    String endpoint,
    {Map<String, dynamic>? body}
  ) async {
    final accessToken = await secureStorage.read(key: 'access_token');

    final response = await http.Request(method, Uri.parse('$baseUrl$endpoint'))
      ..headers.addAll({
        'Content-Type': 'application/json',
        if (accessToken != null) 'Authorization': 'Bearer $accessToken',
      })
      ..body = body != null ? jsonEncode(body) : null;

    final streamedResponse = await response.send();
    final httpResponse = await http.Response.fromStream(streamedResponse);

    // Handle token expiration
    if (httpResponse.statusCode == 401) {
      final data = jsonDecode(httpResponse.body);
      if (data['error_code'] == 'AUTH_002') {
        // Token expired - refresh and retry
        await refreshToken();
        return request(method, endpoint, body: body);
      }
    }

    return httpResponse;
  }
}
```

## Notification Types

The app will receive these notification types via FCM:

| Type | Description | Data Fields |
|------|-------------|-------------|
| `transaction_pending` | New transaction needs confirmation | `entity_type: transaction`, `entity_id` |
| `transaction_confirmed` | Transaction confirmed by customer | `entity_type: transaction`, `entity_id` |
| `transaction_rejected` | Transaction rejected by customer | `entity_type: transaction`, `entity_id` |
| `payment_reminder` | Payment due reminder | `entity_type: transaction`, `entity_id` |
| `payment_success` | Payment completed | `entity_type: payment`, `entity_id` |
| `credit_alert` | Credit limit/health alert | - |
| `settlement_ready` | Settlement ready for payout (merchant) | `entity_type: settlement`, `entity_id` |

## Required Flutter Packages

```yaml
dependencies:
  http: ^1.1.0
  flutter_secure_storage: ^9.0.0
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
  flutter_inappwebview: ^6.0.0
  device_info_plus: ^9.1.0
  provider: ^6.1.0  # or riverpod for state management
```

## Testing

### Test Credentials

For development/testing:
- Customer Bariq ID: `123456`
- Customer Password: `test123`
- Test Card: `4000000000000002` (PayTabs sandbox)

### API Testing

Use the provided Postman collection or test with curl:

```bash
# Login
curl -X POST http://localhost:5001/api/v1/auth/customer/login \
  -H "Content-Type: application/json" \
  -d '{"bariq_id": "123456", "password": "test123"}'

# Get profile (with token)
curl http://localhost:5001/api/v1/customers/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Support

For API issues, contact the backend team or check:
- API docs: `/api/v1/docs` (when enabled)
- Status: `/api/v1/health`
