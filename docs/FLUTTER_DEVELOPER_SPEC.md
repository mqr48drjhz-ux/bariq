# Bariq Al-Yusr - Flutter Developer Specification

## Overview

This document provides detailed specifications for implementing:
1. **Firebase Cloud Messaging (FCM)** - Push notifications
2. **PayTabs Payment Gateway** - Online payments

---

# Part 1: Firebase Cloud Messaging (FCM)

## 1.1 How It Works

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter App   │───▶│  Firebase FCM   │───▶│  Bariq Backend  │
│                 │◀───│                 │◀───│                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘

Flow:
1. App gets FCM token from Firebase
2. App sends token to Bariq backend (device registration)
3. Backend stores token in database
4. When event happens (new transaction, payment, etc.)
5. Backend sends push notification via Firebase
6. Firebase delivers to user's device
```

## 1.2 Firebase Project Setup (Required from Flutter Dev)

### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create new project: "Bariq Al-Yusr"
3. Enable Cloud Messaging

### Step 2: Add Apps to Firebase
- Add Android app (package name: `com.bariq.customer` / `com.bariq.merchant`)
- Add iOS app (bundle ID: `com.bariq.customer` / `com.bariq.merchant`)
- Download config files:
  - `google-services.json` (Android)
  - `GoogleService-Info.plist` (iOS)

### Step 3: Generate Service Account Key (For Backend)
1. Firebase Console → Project Settings → Service Accounts
2. Click "Generate new private key"
3. Send this JSON file to backend developer (me)
4. I will add it to server as `FIREBASE_CREDENTIALS_PATH` or `FIREBASE_CREDENTIALS_JSON`

## 1.3 Flutter Dependencies

```yaml
# pubspec.yaml
dependencies:
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
  flutter_local_notifications: ^16.1.0  # For foreground notifications
  device_info_plus: ^9.1.0              # For device name
```

## 1.4 Flutter Implementation

### 1.4.1 Initialize Firebase

```dart
// main.dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

// Background message handler (MUST be top-level function)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('Background message: ${message.messageId}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  // Set background handler
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  runApp(MyApp());
}
```

### 1.4.2 Push Notification Service

```dart
// services/push_notification_service.dart
import 'dart:io';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:device_info_plus/device_info_plus.dart';

class PushNotificationService {
  static final PushNotificationService _instance = PushNotificationService._internal();
  factory PushNotificationService() => _instance;
  PushNotificationService._internal();

  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();

  String? _fcmToken;
  String get fcmToken => _fcmToken ?? '';

  /// Initialize push notifications
  Future<void> initialize() async {
    // Request permission
    await _requestPermission();

    // Initialize local notifications (for foreground)
    await _initializeLocalNotifications();

    // Get FCM token
    _fcmToken = await _fcm.getToken();
    print('FCM Token: $_fcmToken');

    // Listen for token refresh
    _fcm.onTokenRefresh.listen((newToken) {
      _fcmToken = newToken;
      _onTokenRefresh(newToken);
    });

    // Handle messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);

    // Check if app opened from notification
    RemoteMessage? initialMessage = await _fcm.getInitialMessage();
    if (initialMessage != null) {
      _handleNotificationTap(initialMessage);
    }
  }

  Future<void> _requestPermission() async {
    NotificationSettings settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    print('Permission status: ${settings.authorizationStatus}');
  }

  Future<void> _initializeLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (response) {
        // Handle notification tap from local notification
        _handleLocalNotificationTap(response.payload);
      },
    );

    // Create notification channel for Android
    const androidChannel = AndroidNotificationChannel(
      'bariq_channel',
      'Bariq Notifications',
      description: 'Notifications from Bariq Al-Yusr',
      importance: Importance.high,
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(androidChannel);
  }

  /// Handle foreground messages - show local notification
  void _handleForegroundMessage(RemoteMessage message) {
    print('Foreground message: ${message.notification?.title}');

    RemoteNotification? notification = message.notification;
    if (notification != null) {
      _localNotifications.show(
        notification.hashCode,
        notification.title,
        notification.body,
        NotificationDetails(
          android: AndroidNotificationDetails(
            'bariq_channel',
            'Bariq Notifications',
            importance: Importance.high,
            priority: Priority.high,
            icon: '@mipmap/ic_launcher',
          ),
          iOS: const DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
        payload: message.data.toString(),
      );
    }
  }

  /// Handle notification tap (app in background/terminated)
  void _handleNotificationTap(RemoteMessage message) {
    print('Notification tapped: ${message.data}');
    _navigateBasedOnData(message.data);
  }

  /// Handle local notification tap
  void _handleLocalNotificationTap(String? payload) {
    print('Local notification tapped: $payload');
    // Parse payload and navigate
  }

  /// Navigate based on notification data
  void _navigateBasedOnData(Map<String, dynamic> data) {
    final notificationType = data['notification_type'];
    final entityType = data['entity_type'];
    final entityId = data['entity_id'];

    switch (notificationType) {
      case 'transaction_pending':
        // Navigate to transaction confirmation screen
        // Navigator.pushNamed(context, '/transactions/$entityId');
        break;
      case 'payment_success':
        // Navigate to payment details
        // Navigator.pushNamed(context, '/payments/$entityId');
        break;
      case 'payment_reminder':
        // Navigate to payment screen
        // Navigator.pushNamed(context, '/pay');
        break;
      case 'credit_alert':
        // Navigate to credit screen
        // Navigator.pushNamed(context, '/credit');
        break;
      // Merchant notifications
      case 'transaction_confirmed':
      case 'transaction_rejected':
        // Navigate to transaction details
        break;
      case 'settlement_ready':
        // Navigate to settlements
        break;
    }
  }

  /// Called when token refreshes
  void _onTokenRefresh(String newToken) {
    // Re-register device with backend
    // ApiService.registerDevice(newToken);
  }

  /// Get device info for registration
  Future<Map<String, String>> getDeviceInfo() async {
    final deviceInfo = DeviceInfoPlugin();
    String deviceName = 'Unknown';
    String deviceId = '';
    String deviceType = Platform.isIOS ? 'ios' : 'android';

    if (Platform.isAndroid) {
      final androidInfo = await deviceInfo.androidInfo;
      deviceName = '${androidInfo.brand} ${androidInfo.model}';
      deviceId = androidInfo.id;
    } else if (Platform.isIOS) {
      final iosInfo = await deviceInfo.iosInfo;
      deviceName = iosInfo.name;
      deviceId = iosInfo.identifierForVendor ?? '';
    }

    return {
      'device_name': deviceName,
      'device_id': deviceId,
      'device_type': deviceType,
    };
  }
}
```

### 1.4.3 Device Registration API

```dart
// services/api_service.dart
class ApiService {
  static const String baseUrl = 'https://your-api.com/api/v1';

  /// Register device for push notifications
  /// Call this after login and whenever FCM token refreshes
  static Future<bool> registerDevice() async {
    final pushService = PushNotificationService();
    final fcmToken = pushService.fcmToken;

    if (fcmToken.isEmpty) return false;

    final deviceInfo = await pushService.getDeviceInfo();
    final accessToken = await SecureStorage.read('access_token');

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/customers/me/devices'),  // or /merchants/me/devices
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $accessToken',
        },
        body: jsonEncode({
          'fcm_token': fcmToken,
          'device_type': deviceInfo['device_type'],
          'device_name': deviceInfo['device_name'],
          'device_id': deviceInfo['device_id'],
        }),
      );

      return response.statusCode == 201;
    } catch (e) {
      print('Device registration failed: $e');
      return false;
    }
  }

  /// Unregister device (call on logout)
  static Future<void> unregisterDevice(String deviceId) async {
    final accessToken = await SecureStorage.read('access_token');

    await http.delete(
      Uri.parse('$baseUrl/customers/me/devices/$deviceId'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
  }
}
```

## 1.5 Notification Types Reference

| Type | When Sent | Data Fields | Action |
|------|-----------|-------------|--------|
| `transaction_pending` | New transaction created | `entity_type: transaction`, `entity_id` | Go to confirm transaction |
| `transaction_confirmed` | Customer confirms | `entity_type: transaction`, `entity_id` | Show transaction details |
| `transaction_rejected` | Customer rejects | `entity_type: transaction`, `entity_id` | Show transaction details |
| `payment_reminder` | Payment due soon | `entity_type: transaction`, `entity_id` | Go to payment screen |
| `payment_success` | Payment completed | `entity_type: payment`, `entity_id` | Show payment receipt |
| `credit_alert` | Credit limit change | - | Go to credit screen |
| `settlement_ready` | Settlement available | `entity_type: settlement`, `entity_id` | Go to settlements |

---

# Part 2: PayTabs Payment Gateway

## 2.1 How It Works

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter App   │───▶│  Bariq Backend  │───▶│    PayTabs      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │
        │  1. Initiate Payment │                      │
        │─────────────────────▶│                      │
        │                      │  2. Create Payment   │
        │                      │─────────────────────▶│
        │                      │  3. Payment URL      │
        │                      │◀─────────────────────│
        │  4. Return URL       │                      │
        │◀─────────────────────│                      │
        │                      │                      │
        │  5. Open WebView     │                      │
        │─────────────────────────────────────────────▶
        │                      │                      │
        │  6. User Pays        │                      │
        │◀─────────────────────────────────────────────│
        │                      │                      │
        │  7. Redirect to App  │  8. Webhook          │
        │◀─────────────────────│◀─────────────────────│
        │                      │                      │
        │  9. Check Status     │                      │
        │─────────────────────▶│                      │
```

## 2.2 Flutter Dependencies

```yaml
# pubspec.yaml
dependencies:
  flutter_inappwebview: ^6.0.0  # For payment WebView
  # OR
  webview_flutter: ^4.4.0       # Alternative WebView
```

## 2.3 Flutter Implementation

### 2.3.1 Payment Service

```dart
// services/payment_service.dart
class PaymentService {
  static const String baseUrl = 'https://your-api.com/api/v1';

  /// Initiate payment - returns URL to open in WebView
  static Future<PaymentInitResponse> initiatePayment({
    required List<String> transactionIds,
    required double amount,
    String paymentMethod = 'all',
  }) async {
    final accessToken = await SecureStorage.read('access_token');

    final response = await http.post(
      Uri.parse('$baseUrl/customers/me/payments/initiate'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
      body: jsonEncode({
        'transaction_ids': transactionIds,
        'amount': amount,
        'payment_method': paymentMethod,
      }),
    );

    final data = jsonDecode(response.body);
    return PaymentInitResponse.fromJson(data);
  }

  /// Check payment status
  static Future<PaymentStatus> checkStatus(String paymentId) async {
    final accessToken = await SecureStorage.read('access_token');

    final response = await http.get(
      Uri.parse('$baseUrl/customers/me/payments/$paymentId/status'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );

    return PaymentStatus.fromJson(jsonDecode(response.body));
  }

  /// Get available payment methods
  static Future<List<PaymentMethod>> getPaymentMethods() async {
    final accessToken = await SecureStorage.read('access_token');

    final response = await http.get(
      Uri.parse('$baseUrl/customers/me/payment-methods'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );

    final data = jsonDecode(response.body);
    return (data['data']['methods'] as List)
        .map((m) => PaymentMethod.fromJson(m))
        .toList();
  }
}

// Models
class PaymentInitResponse {
  final bool success;
  final String? paymentUrl;
  final String? paymentId;
  final String? tranRef;
  final String? message;

  PaymentInitResponse({
    required this.success,
    this.paymentUrl,
    this.paymentId,
    this.tranRef,
    this.message,
  });

  factory PaymentInitResponse.fromJson(Map<String, dynamic> json) {
    return PaymentInitResponse(
      success: json['success'] ?? false,
      paymentUrl: json['data']?['payment_url'],
      paymentId: json['data']?['payment_id'],
      tranRef: json['data']?['tran_ref'],
      message: json['message'],
    );
  }
}

class PaymentStatus {
  final String status;  // pending, completed, failed
  final double amount;
  final String? gatewayReference;

  PaymentStatus({
    required this.status,
    required this.amount,
    this.gatewayReference,
  });

  factory PaymentStatus.fromJson(Map<String, dynamic> json) {
    return PaymentStatus(
      status: json['data']?['status'] ?? 'unknown',
      amount: (json['data']?['amount'] ?? 0).toDouble(),
      gatewayReference: json['data']?['gateway_reference'],
    );
  }
}
```

### 2.3.2 Payment WebView Screen

```dart
// screens/payment_webview_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

class PaymentWebViewScreen extends StatefulWidget {
  final String paymentUrl;
  final String paymentId;

  const PaymentWebViewScreen({
    required this.paymentUrl,
    required this.paymentId,
    Key? key,
  }) : super(key: key);

  @override
  State<PaymentWebViewScreen> createState() => _PaymentWebViewScreenState();
}

class _PaymentWebViewScreenState extends State<PaymentWebViewScreen> {
  late InAppWebViewController _controller;
  bool _isLoading = true;

  @override
  Widget build(BuildContext context) {
    return WillPopScope(
      onWillPop: () async {
        // Confirm before closing
        final shouldClose = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('إلغاء الدفع؟'),
            content: Text('هل تريد إلغاء عملية الدفع؟'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: Text('لا'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text('نعم'),
              ),
            ],
          ),
        );
        return shouldClose ?? false;
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text('الدفع'),
          leading: IconButton(
            icon: Icon(Icons.close),
            onPressed: () => _confirmClose(),
          ),
        ),
        body: Stack(
          children: [
            InAppWebView(
              initialUrlRequest: URLRequest(
                url: WebUri(widget.paymentUrl),
              ),
              initialOptions: InAppWebViewGroupOptions(
                crossPlatform: InAppWebViewOptions(
                  useShouldOverrideUrlLoading: true,
                  javaScriptEnabled: true,
                ),
              ),
              onWebViewCreated: (controller) {
                _controller = controller;

                // Add JavaScript handler for payment completion
                controller.addJavaScriptHandler(
                  handlerName: 'paymentComplete',
                  callback: (args) {
                    if (args.isNotEmpty) {
                      final message = args[0] as Map<String, dynamic>;
                      _handlePaymentComplete(message);
                    }
                  },
                );
              },
              onLoadStart: (controller, url) {
                setState(() => _isLoading = true);
              },
              onLoadStop: (controller, url) async {
                setState(() => _isLoading = false);

                // Check if on completion page
                final currentUrl = url.toString();
                if (currentUrl.contains('/payment/complete')) {
                  // The page will call our JavaScript handler
                  // But we can also check URL params as backup
                }
              },
              shouldOverrideUrlLoading: (controller, navigationAction) async {
                final url = navigationAction.request.url.toString();

                // Handle deep links or custom schemes
                if (url.startsWith('bariq://')) {
                  _handleDeepLink(url);
                  return NavigationActionPolicy.CANCEL;
                }

                return NavigationActionPolicy.ALLOW;
              },
            ),
            if (_isLoading)
              Center(
                child: CircularProgressIndicator(),
              ),
          ],
        ),
      ),
    );
  }

  void _handlePaymentComplete(Map<String, dynamic> message) {
    final success = message['success'] as bool? ?? false;
    final status = message['status'] as String? ?? '';
    final tranRef = message['tranRef'] as String?;

    Navigator.pop(context, PaymentResult(
      success: success,
      status: status,
      tranRef: tranRef,
    ));
  }

  void _handleDeepLink(String url) {
    // Parse deep link and handle
    final uri = Uri.parse(url);
    if (uri.host == 'payment-complete') {
      final success = uri.queryParameters['success'] == 'true';
      Navigator.pop(context, PaymentResult(
        success: success,
        status: uri.queryParameters['status'] ?? '',
        tranRef: uri.queryParameters['tran_ref'],
      ));
    }
  }

  Future<void> _confirmClose() async {
    final shouldClose = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('إلغاء الدفع؟'),
        content: Text('هل تريد إلغاء عملية الدفع؟'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('لا'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('نعم'),
          ),
        ],
      ),
    );

    if (shouldClose == true) {
      Navigator.pop(context, PaymentResult(
        success: false,
        status: 'cancelled',
      ));
    }
  }
}

class PaymentResult {
  final bool success;
  final String status;
  final String? tranRef;

  PaymentResult({
    required this.success,
    required this.status,
    this.tranRef,
  });
}
```

### 2.3.3 Payment Flow Usage

```dart
// Example: Pay for transactions
class PaymentScreen extends StatefulWidget {
  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  List<Transaction> _selectedTransactions = [];
  double _paymentAmount = 0;
  bool _isLoading = false;

  Future<void> _startPayment() async {
    if (_selectedTransactions.isEmpty || _paymentAmount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('الرجاء اختيار المعاملات وإدخال المبلغ')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // 1. Initiate payment with backend
      final response = await PaymentService.initiatePayment(
        transactionIds: _selectedTransactions.map((t) => t.id).toList(),
        amount: _paymentAmount,
        paymentMethod: 'all',  // or 'mada', 'creditcard', etc.
      );

      if (!response.success || response.paymentUrl == null) {
        throw Exception(response.message ?? 'فشل في إنشاء الدفع');
      }

      // 2. Open payment WebView
      final result = await Navigator.push<PaymentResult>(
        context,
        MaterialPageRoute(
          builder: (context) => PaymentWebViewScreen(
            paymentUrl: response.paymentUrl!,
            paymentId: response.paymentId!,
          ),
        ),
      );

      // 3. Handle result
      if (result != null) {
        if (result.success) {
          _showSuccessDialog();
        } else if (result.status == 'cancelled') {
          // User cancelled - do nothing
        } else {
          _showFailureDialog(result.status);
        }
      }

    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('حدث خطأ: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green),
            SizedBox(width: 8),
            Text('تم الدفع بنجاح'),
          ],
        ),
        content: Text('تم استلام دفعتك بنجاح'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);  // Go back to previous screen
            },
            child: Text('حسناً'),
          ),
        ],
      ),
    );
  }

  void _showFailureDialog(String status) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.error, color: Colors.red),
            SizedBox(width: 8),
            Text('فشل الدفع'),
          ],
        ),
        content: Text('عذراً، لم تتم عملية الدفع. يرجى المحاولة مرة أخرى.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('حسناً'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // ... your UI
  }
}
```

## 2.4 Payment Methods Available

| Method | Code | Icon |
|--------|------|------|
| All Methods | `all` | - |
| Credit Card (Visa/MC) | `creditcard` | 💳 |
| Mada | `mada` | 🏦 |
| STC Pay | `stcpay` | 📱 |
| Apple Pay | `applepay` | 🍎 |

## 2.5 Test Cards (Sandbox)

| Card Type | Number | Expiry | CVV |
|-----------|--------|--------|-----|
| Visa (Success) | `4000000000000002` | Any future | Any 3 digits |
| Mastercard | `5200000000000007` | Any future | Any 3 digits |
| Mada | `4464040000000007` | Any future | Any 3 digits |

**Test OTP:** `123456`

---

# Part 3: Required Screens

## 3.1 Customer App Screens

### Screen 1: Home Dashboard
- Credit balance card
- Quick actions (Pay, View transactions)
- Recent notifications

### Screen 2: Transactions List
- List of all transactions
- Filter by status (pending, active, completed)
- Pull to refresh

### Screen 3: Transaction Details
- Transaction info (merchant, amount, date)
- Payment progress
- Confirm/Reject buttons (for pending)

### Screen 4: Transaction Confirmation
- Show transaction details
- Confirm or Reject buttons
- Rejection reason input

### Screen 5: Payment Screen
- Select transactions to pay
- Enter amount
- Select payment method
- Pay button → Opens WebView

### Screen 6: Payment WebView
- PayTabs hosted page
- Loading indicator
- Back confirmation dialog

### Screen 7: Payment Success/Failure
- Success/failure icon
- Amount and reference
- Back to home button

### Screen 8: Notifications List
- List of notifications
- Mark as read
- Tap to navigate

### Screen 9: Credit Details
- Credit limit
- Used/Available credit
- Request increase button

### Screen 10: Profile Settings
- Personal info
- Change password
- Notification settings
- Logout

## 3.2 Merchant App Screens

### Screen 1: Dashboard
- Today's sales
- Pending transactions
- Quick create transaction

### Screen 2: Create Transaction
- Search customer by Bariq ID
- Enter amount and description
- Submit transaction

### Screen 3: Transactions List
- Filter by status
- Search by reference/customer

### Screen 4: Transaction Details
- Full transaction info
- Status history
- Cancel button (if pending)

### Screen 5: Staff Management (Admin)
- List staff members
- Add/Edit staff
- Assign roles and branches

### Screen 6: Reports
- Sales summary
- Transaction reports
- Export options

### Screen 7: Settlements
- Settlement list
- Settlement details
- Status tracking

### Screen 8: Notifications
- Staff notifications
- Mark as read

### Screen 9: Profile/Settings
- Merchant info
- Staff profile
- Logout

---

# Part 4: API Endpoints Summary

## Authentication
```
POST /api/v1/auth/customer/login          # Customer login
POST /api/v1/auth/customer/refresh        # Refresh token
POST /api/v1/auth/merchant/login          # Merchant login
POST /api/v1/auth/merchant/refresh        # Refresh token
```

## Customer
```
GET  /api/v1/customers/me                 # Profile
PUT  /api/v1/customers/me                 # Update profile
GET  /api/v1/customers/me/credit          # Credit details
GET  /api/v1/customers/me/transactions    # Transactions list
POST /api/v1/customers/me/transactions/{id}/confirm
POST /api/v1/customers/me/transactions/{id}/reject
GET  /api/v1/customers/me/debt            # Debt summary
GET  /api/v1/customers/me/notifications   # Notifications
POST /api/v1/customers/me/devices         # Register device
DELETE /api/v1/customers/me/devices/{id}  # Unregister device
POST /api/v1/customers/me/payments/initiate  # Start payment
GET  /api/v1/customers/me/payments/{id}/status
```

## Merchant
```
GET  /api/v1/merchants/me                 # Profile
POST /api/v1/merchants/me/transactions    # Create transaction
GET  /api/v1/merchants/me/transactions    # List transactions
GET  /api/v1/merchants/me/staff           # List staff
POST /api/v1/merchants/me/staff           # Create staff
GET  /api/v1/merchants/me/notifications   # Notifications
POST /api/v1/merchants/me/devices         # Register device
```

---

# Part 5: Checklist for Flutter Developer

## Firebase Setup
- [ ] Create Firebase project
- [ ] Add Android app with package name
- [ ] Add iOS app with bundle ID
- [ ] Download and add `google-services.json` (Android)
- [ ] Download and add `GoogleService-Info.plist` (iOS)
- [ ] Generate service account key and send to backend developer
- [ ] Enable Cloud Messaging in Firebase Console

## Push Notifications
- [ ] Add firebase_messaging dependency
- [ ] Add flutter_local_notifications dependency
- [ ] Initialize Firebase on app start
- [ ] Request notification permissions
- [ ] Get and store FCM token
- [ ] Register device with backend after login
- [ ] Handle foreground notifications
- [ ] Handle background notifications
- [ ] Handle notification tap navigation
- [ ] Unregister device on logout

## Payments
- [ ] Add flutter_inappwebview dependency
- [ ] Create payment initiation API call
- [ ] Create WebView screen for payments
- [ ] Add JavaScript handler for payment completion
- [ ] Handle payment success/failure
- [ ] Show appropriate dialogs

## General
- [ ] Implement secure token storage
- [ ] Add token refresh logic
- [ ] Handle API errors
- [ ] Add Arabic/English localization
- [ ] Test on real devices (not just emulator)

---

# Questions?

Contact backend developer for:
- Firebase service account key setup
- API authentication issues
- Webhook testing
- Sandbox credentials
