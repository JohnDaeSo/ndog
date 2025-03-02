// swift-tools-version:5.5
import PackageDescription

let package = Package(
    name: "MacDog",
    platforms: [
        .macOS(.v11)
    ],
    products: [
        .executable(name: "macdog", targets: ["MacDog"]),
        .library(name: "MacDogCore", targets: ["MacDogCore"])
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.1.0"),
        .package(url: "https://github.com/apple/swift-log.git", from: "1.4.2"),
        .package(url: "https://github.com/sparkle-project/Sparkle", from: "2.0.0")
    ],
    targets: [
        // Command line tool
        .executableTarget(
            name: "MacDog",
            dependencies: [
                "MacDogCore",
                .product(name: "ArgumentParser", package: "swift-argument-parser")
            ]
        ),
        
        // Core functionality library
        .target(
            name: "MacDogCore",
            dependencies: [
                .product(name: "Logging", package: "swift-log")
            ]
        ),
        
        // GUI application target
        .target(
            name: "MacDogGUI",
            dependencies: [
                "MacDogCore",
                .product(name: "Sparkle", package: "Sparkle")
            ]
        ),
        
        // Tests
        .testTarget(
            name: "MacDogTests",
            dependencies: ["MacDogCore"]
        )
    ]
) 