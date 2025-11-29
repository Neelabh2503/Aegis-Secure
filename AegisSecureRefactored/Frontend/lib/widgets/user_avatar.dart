import 'dart:convert';
import 'package:flutter/material.dart';

class UserAvatar extends StatelessWidget {
  final String? avatarBase64;
  final String? userName;
  final Color? backgroundColor;
  final VoidCallback? onTap;
  final double radius;

  const UserAvatar({
    Key? key,
    this.avatarBase64,
    this.userName,
    this.backgroundColor,
    this.onTap,
    this.radius = 20,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final String initial = (userName != null && userName!.isNotEmpty)
        ? userName![0].toUpperCase()
        : '?';
    
    final bgColor = backgroundColor ?? Theme.of(context).primaryColor;

    Widget avatar = CircleAvatar(
      radius: radius,
      backgroundColor: bgColor,
      backgroundImage: avatarBase64 != null && avatarBase64!.isNotEmpty
          ? MemoryImage(base64Decode(avatarBase64!))
          : null,
      child: avatarBase64 == null || avatarBase64!.isEmpty
          ? Text(
              initial,
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: radius * 0.6,
              ),
            )
          : null,
    );

    if (onTap != null) {
      return GestureDetector(
        onTap: onTap,
        child: avatar,
      );
    }

    return avatar;
  }
}
