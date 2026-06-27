import "package:camera/camera.dart";
import "package:flutter/material.dart";

import "screens/camera_screen.dart";
import "theme.dart";

late List<CameraDescription> cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    cameras = await availableCameras();
  } catch (_) {
    cameras = [];
  }
  runApp(const HazardApp());
}

class HazardApp extends StatelessWidget {
  const HazardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Campus Hazard Detection",
      debugShowCheckedModeBanner: false,
      theme: Hud.themeData(),
      home: CameraScreen(cameras: cameras),
    );
  }
}
