import Foundation
import Logging

/// Manages file transfer operations with progress tracking
public class FileTransfer {
    // MARK: - Properties
    
    private let logger = Logger(label: "com.macdog.FileTransfer")
    private let networkManager: NetworkManager
    private let fileChunkSize: Int
    
    // Progress tracking
    public var onProgressUpdated: ((Double) -> Void)?
    public var onTransferCompleted: ((URL) -> Void)?
    public var onTransferFailed: ((Error) -> Void)?
    
    // MARK: - Initialization
    
    /// Initialize with a network manager and optional chunk size
    /// - Parameters:
    ///   - networkManager: The network manager to use for transfers
    ///   - fileChunkSize: The size of chunks to use when sending files
    public init(networkManager: NetworkManager, fileChunkSize: Int = 1024 * 64) {
        self.networkManager = networkManager
        self.fileChunkSize = fileChunkSize
    }
    
    // MARK: - Public Methods
    
    /// Send a file with progress updates
    /// - Parameter filePath: The path to the file to send
    public func sendFile(atPath filePath: String) {
        let fileURL = URL(fileURLWithPath: filePath)
        sendFile(at: fileURL)
    }
    
    /// Send a file with progress updates
    /// - Parameter fileURL: The URL of the file to send
    public func sendFile(at fileURL: URL) {
        do {
            // Get file size for progress tracking
            let fileAttributes = try FileManager.default.attributesOfItem(atPath: fileURL.path)
            guard let fileSize = fileAttributes[.size] as? Int64, fileSize > 0 else {
                let error = NSError(domain: "com.macdog", code: 100, userInfo: [NSLocalizedDescriptionKey: "Invalid file size"])
                logger.error("Invalid file size for \(fileURL.path)")
                onTransferFailed?(error)
                return
            }
            
            logger.info("Starting file transfer: \(fileURL.lastPathComponent) (\(fileSize) bytes)")
            
            // We'll send the file in chunks for better progress tracking
            // First, send the file metadata
            let metadataString = "FILE:\(fileURL.lastPathComponent):\(fileSize)"
            guard let metadataData = metadataString.data(using: .utf8) else {
                let error = NSError(domain: "com.macdog", code: 101, userInfo: [NSLocalizedDescriptionKey: "Failed to encode file metadata"])
                logger.error("Failed to encode file metadata")
                onTransferFailed?(error)
                return
            }
            
            // Send the metadata
            networkManager.send(data: metadataData) { [weak self] error in
                guard let self = self else { return }
                
                if let error = error {
                    self.logger.error("Failed to send file metadata: \(error)")
                    self.onTransferFailed?(error)
                    return
                }
                
                // Start sending the file in chunks
                self.sendFileChunks(fileURL: fileURL, fileSize: fileSize)
            }
        } catch {
            logger.error("Failed to prepare file for sending: \(error)")
            onTransferFailed?(error)
        }
    }
    
    /// Receive a file with progress updates
    /// - Parameter savePath: The path where the received file should be saved
    public func receiveFile(saveAt savePath: String) {
        // Make sure the save directory exists
        let saveURL = URL(fileURLWithPath: savePath)
        let saveDirectory = saveURL.deletingLastPathComponent()
        
        do {
            try FileManager.default.createDirectory(at: saveDirectory, withIntermediateDirectories: true)
        } catch {
            logger.error("Failed to create save directory: \(error)")
            onTransferFailed?(error)
            return
        }
        
        // Setup the file metadata handler
        var fileMetadataReceived = false
        var receivedFileName: String?
        var expectedFileSize: Int64 = 0
        var bytesReceived: Int64 = 0
        var fileOutputStream: OutputStream?
        
        // Setup data handler
        networkManager.onDataReceived = { [weak self] data in
            guard let self = self else { return }
            
            // If we haven't received file metadata yet
            if !fileMetadataReceived {
                // Try to interpret the data as file metadata
                if let metadataString = String(data: data, encoding: .utf8), metadataString.hasPrefix("FILE:") {
                    // Parse the metadata (format: FILE:filename:size)
                    let components = metadataString.components(separatedBy: ":")
                    if components.count >= 3 {
                        receivedFileName = components[1]
                        expectedFileSize = Int64(components[2]) ?? 0
                        
                        // Create the save path
                        let finalSavePath: String
                        if FileManager.default.fileExists(atPath: savePath) && FileManager.default.isDirectory(atPath: savePath) {
                            // If savePath is a directory, use the original filename
                            finalSavePath = savePath + "/" + (receivedFileName ?? "received_file")
                        } else {
                            // Use the specified path as-is
                            finalSavePath = savePath
                        }
                        
                        // Create the output stream
                        fileOutputStream = OutputStream(toFileAtPath: finalSavePath, append: false)
                        fileOutputStream?.open()
                        
                        fileMetadataReceived = true
                        logger.info("File metadata received: \(receivedFileName ?? "unknown") (\(expectedFileSize) bytes)")
                        
                        // Skip the rest of this callback as we've just processed metadata
                        return
                    }
                }
            }
            
            // Handle file data
            if fileMetadataReceived, let outputStream = fileOutputStream {
                // Write the data to the file
                let bytesWritten = data.withUnsafeBytes { bufferPointer in
                    outputStream.write(bufferPointer.baseAddress!.assumingMemoryBound(to: UInt8.self), maxLength: data.count)
                }
                
                if bytesWritten < 0 {
                    // Writing error
                    let error = outputStream.streamError ?? NSError(domain: "com.macdog", code: 102, userInfo: [NSLocalizedDescriptionKey: "Failed to write to file"])
                    self.logger.error("Failed to write to file: \(error)")
                    self.onTransferFailed?(error)
                    return
                }
                
                // Update progress
                bytesReceived += Int64(bytesWritten)
                let progress = Double(bytesReceived) / Double(expectedFileSize)
                self.onProgressUpdated?(progress)
                
                // Check if we've received the entire file
                if bytesReceived >= expectedFileSize {
                    // Close the file
                    outputStream.close()
                    fileOutputStream = nil
                    
                    // Notify completion
                    let finalURL = URL(fileURLWithPath: savePath)
                    self.logger.info("File transfer completed: \(finalURL.path)")
                    self.onTransferCompleted?(finalURL)
                    
                    // Reset for potential future transfers
                    fileMetadataReceived = false
                    receivedFileName = nil
                    expectedFileSize = 0
                    bytesReceived = 0
                }
            }
        }
        
        // Start receiving data
        networkManager.startReceiving()
    }
    
    // MARK: - Private Methods
    
    private func sendFileChunks(fileURL: URL, fileSize: Int64) {
        do {
            // Open the file for reading
            let fileInputStream = InputStream(url: fileURL)
            fileInputStream?.open()
            defer { fileInputStream?.close() }
            
            guard let inputStream = fileInputStream else {
                throw NSError(domain: "com.macdog", code: 103, userInfo: [NSLocalizedDescriptionKey: "Failed to open file for reading"])
            }
            
            // Create a buffer for reading chunks
            var buffer = [UInt8](repeating: 0, count: fileChunkSize)
            var totalBytesSent: Int64 = 0
            
            // Send the file in chunks
            while inputStream.hasBytesAvailable {
                let bytesRead = inputStream.read(&buffer, maxLength: fileChunkSize)
                
                if bytesRead < 0 {
                    // Reading error
                    if let error = inputStream.streamError {
                        throw error
                    } else {
                        throw NSError(domain: "com.macdog", code: 104, userInfo: [NSLocalizedDescriptionKey: "Failed to read from file"])
                    }
                }
                
                if bytesRead > 0 {
                    let chunkData = Data(bytes: buffer, count: bytesRead)
                    
                    // Send this chunk
                    let semaphore = DispatchSemaphore(value: 0)
                    var chunkError: Error?
                    
                    networkManager.send(data: chunkData) { error in
                        chunkError = error
                        semaphore.signal()
                    }
                    
                    // Wait for the chunk to be sent
                    _ = semaphore.wait(timeout: .now() + 30.0)
                    
                    // Check for error
                    if let error = chunkError {
                        throw error
                    }
                    
                    // Update progress
                    totalBytesSent += Int64(bytesRead)
                    let progress = Double(totalBytesSent) / Double(fileSize)
                    onProgressUpdated?(progress)
                    
                    logger.debug("Sent chunk: \(bytesRead) bytes, total progress: \(Int(progress * 100))%")
                    
                    // If we've sent all bytes, we're done
                    if totalBytesSent >= fileSize {
                        logger.info("File transfer completed: \(fileURL.path)")
                        onTransferCompleted?(fileURL)
                        break
                    }
                }
            }
            
        } catch {
            logger.error("Error sending file chunks: \(error)")
            onTransferFailed?(error)
        }
    }
} 