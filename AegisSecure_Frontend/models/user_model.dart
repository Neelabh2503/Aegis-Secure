// This file defines a simple data model for a user. 
// It helps represent a user object with an id, email and name.
// It also provides an easy way to convert Json data into a user instance.

class User {
  // final means that once the vaules are set, they cannot be changed.
  final String id; 
  final String email; 
  final String name; 

  // Constructor for creating a user object.
  // required means that all three fields must be provided when creating a user/
  User({required this.id, required this.email, required this.name});

  // this is a factory constructor that creates a user object from Json data.
  factory User.fromJson(Map<String, dynamic> json) {
    // the keys here should match the keys in the Json data. 
    // If any key is missing then an empty string is used as default value.
    return User(
      id: json['_id'] ?? '',
      email: json['email'] ?? '',
      name: json['name'] ?? '',
    );
  }
}

