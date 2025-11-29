class User {
  final String id;
  final String email;
  final String name;
  final String? avatarBase64;

  const User({
    required this.id,
    required this.email,
    required this.name,
    this.avatarBase64,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['user_id'] ?? '',
      email: json['email'] ?? '',
      name: json['name'] ?? '',
      avatarBase64: json['avatar_base64'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': id,
      'email': email,
      'name': name,
      'avatar_base64': avatarBase64,
    };
  }

  User copyWith({
    String? id,
    String? email,
    String? name,
    String? avatarBase64,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      name: name ?? this.name,
      avatarBase64: avatarBase64 ?? this.avatarBase64,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is User &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          email == other.email &&
          name == other.name;

  @override
  int get hashCode => id.hashCode ^ email.hashCode ^ name.hashCode;

  @override
  String toString() => 'User(id: $id, email: $email, name: $name)';
}
