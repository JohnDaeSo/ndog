import Foundation
import Network
import Logging

/// Main class responsible for network operations
public class NetworkManager {
    // MARK: - Properties
    
    private let logger = Logger(label: "com.macdog.NetworkManager")
    private var connection: NWConnection?
    private var listener: NWListener?
    private var connectionQueue = DispatchQueue(label: "com.macdog.connection-queue")
    
    // Callback handlers
    public var onConnectionStateChanged: ((NWConnection.State) -> Void)?
    public var onDataReceived: ((Data) -> Void)?
    public var onMessageReceived: ((String) -> Void)?
    public var onError: ((Error) -> Void)?
    
    // MARK: - Initialization
    
    public init() {}
    
    // MARK: - Public Methods
    
    /// Connect to a remote host
    /// - Parameters:
    ///   - host: The hostname or IP address to connect to
    ///   - port: The port number to use
    ///   - useUDP: Whether to use UDP instead of TCP
    public func connect(to host: String, port: Int, useUDP: Bool = false) {
        logger.info("Connecting to \(host):\(port) using \(useUDP ? "UDP" : "TCP")")
        
        // Create an NWEndpoint for the remote host
        let hostEndpoint = NWEndpoint.Host(host)
        let portEndpoint = NWEndpoint.Port(integerLiteral: NWEndpoint.Port.IntegerLiteralType(port))
        
        // Choose the appropriate protocol
        let parameters = useUDP ? NWParameters.udp : NWParameters.tcp
        
        // Create the connection
        connection = NWConnection(host: hostEndpoint, port: portEndpoint, using: parameters)
        
        // Set the state update handler
        connection?.stateUpdateHandler = { [weak self] state in
            guard let self = self else { return }
            self.handleConnectionStateChange(state)
        }
        
        // Start the connection
        connection?.start(queue: connectionQueue)
    }
    
    /// Start listening for incoming connections
    /// - Parameters:
    ///   - port: The port number to listen on
    ///   - useUDP: Whether to use UDP instead of TCP
    public func listen(on port: Int, useUDP: Bool = false) throws {
        logger.info("Starting listener on port \(port) using \(useUDP ? "UDP" : "TCP")")
        
        // Choose the appropriate protocol
        let parameters = useUDP ? NWParameters.udp : NWParameters.tcp
        
        // Create the port endpoint
        let portEndpoint = NWEndpoint.Port(integerLiteral: NWEndpoint.Port.IntegerLiteralType(port))
        
        // Create the listener
        do {
            listener = try NWListener(using: parameters, on: portEndpoint)
        } catch {
            logger.error("Failed to create listener: \(error)")
            throw error
        }
        
        // Set up the listener's state update handler
        listener?.stateUpdateHandler = { [weak self] state in
            guard let self = self else { return }
            switch state {
            case .ready:
                self.logger.info("Listener is ready on port \(port)")
                // Notify any observers
                
            case .failed(let error):
                self.logger.error("Listener failed: \(error)")
                self.onError?(error)
                
            default:
                self.logger.info("Listener state changed: \(state)")
            }
        }
        
        // Set up the new connection handler
        listener?.newConnectionHandler = { [weak self] connection in
            guard let self = self else { return }
            self.logger.info("New connection received")
            
            // Handle the new connection
            self.handleNewConnection(connection)
        }
        
        // Start the listener
        listener?.start(queue: connectionQueue)
    }
    
    /// Send data over the current connection
    /// - Parameter data: The data to send
    public func send(data: Data, completion: @escaping (Error?) -> Void) {
        guard let connection = connection else {
            let error = NSError(domain: "com.macdog", code: 1, userInfo: [NSLocalizedDescriptionKey: "No active connection"])
            logger.error("Cannot send data: \(error)")
            completion(error)
            return
        }
        
        connection.send(content: data, completion: .contentProcessed { error in
            if let error = error {
                self.logger.error("Failed to send data: \(error)")
                completion(error)
            } else {
                self.logger.debug("Data sent successfully (\(data.count) bytes)")
                completion(nil)
            }
        })
    }
    
    /// Send a text message over the current connection
    /// - Parameter message: The string message to send
    public func sendMessage(_ message: String, completion: @escaping (Error?) -> Void) {
        guard let data = message.data(using: .utf8) else {
            let error = NSError(domain: "com.macdog", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to encode message"])
            logger.error("Cannot encode message: \(error)")
            completion(error)
            return
        }
        
        // Prepend message type identifier and length
        var messageData = Data()
        // Add "MSG:" prefix to identify this as a text message
        let prefix = "MSG:".data(using: .utf8)!
        messageData.append(prefix)
        messageData.append(data)
        
        send(data: messageData, completion: completion)
    }
    
    /// Send a file over the current connection
    /// - Parameter url: The URL of the file to send
    public func sendFile(at url: URL, completion: @escaping (Error?) -> Void) {
        do {
            // Get file attributes
            let fileAttributes = try FileManager.default.attributesOfItem(atPath: url.path)
            let fileSize = fileAttributes[.size] as! Int64
            
            // Read file data
            let fileData = try Data(contentsOf: url)
            
            // Create file metadata
            let fileName = url.lastPathComponent
            let metadataString = "FILE:\(fileName):\(fileSize)"
            let metadataData = metadataString.data(using: .utf8)!
            
            // Send the metadata first
            send(data: metadataData) { [weak self] error in
                guard let self = self else { return }
                
                if let error = error {
                    self.logger.error("Failed to send file metadata: \(error)")
                    completion(error)
                    return
                }
                
                // Now send the file data
                self.send(data: fileData, completion: completion)
            }
        } catch {
            logger.error("Failed to prepare file for sending: \(error)")
            completion(error)
        }
    }
    
    /// Start receiving data on the current connection
    public func startReceiving() {
        receiveNextData()
    }
    
    /// Close the current connection
    public func disconnect() {
        connection?.cancel()
        connection = nil
        logger.info("Connection closed")
    }
    
    /// Stop the listener
    public func stopListening() {
        listener?.cancel()
        listener = nil
        logger.info("Listener stopped")
    }
    
    // MARK: - Private Methods
    
    private func handleConnectionStateChange(_ state: NWConnection.State) {
        switch state {
        case .ready:
            logger.info("Connection established")
            // Start receiving data
            receiveNextData()
            // Notify observers
            onConnectionStateChanged?(.ready)
            
        case .failed(let error):
            logger.error("Connection failed: \(error)")
            // Notify observers
            onConnectionStateChanged?(.failed(error))
            onError?(error)
            
        case .cancelled:
            logger.info("Connection cancelled")
            // Notify observers
            onConnectionStateChanged?(.cancelled)
            
        default:
            logger.debug("Connection state changed: \(state)")
            // Notify observers
            onConnectionStateChanged?(state)
        }
    }
    
    private func handleNewConnection(_ newConnection: NWConnection) {
        // If we already have a connection, close it
        if connection != nil {
            logger.debug("Replacing existing connection with new one")
            disconnect()
        }
        
        // Set the new connection
        connection = newConnection
        
        // Configure the new connection
        connection?.stateUpdateHandler = { [weak self] state in
            guard let self = self else { return }
            self.handleConnectionStateChange(state)
        }
        
        // Start the connection
        connection?.start(queue: connectionQueue)
    }
    
    private func receiveNextData() {
        connection?.receive(minimumIncompleteLength: 1, maximumLength: 65536) { [weak self] (data, context, isComplete, error) in
            guard let self = self else { return }
            
            if let error = error {
                self.logger.error("Receive error: \(error)")
                self.onError?(error)
                return
            }
            
            if let data = data, !data.isEmpty {
                self.logger.debug("Received \(data.count) bytes")
                
                // Process the received data
                self.processReceivedData(data)
                
                // Continue receiving
                self.receiveNextData()
            } else if isComplete {
                self.logger.info("Receive completed")
            }
        }
    }
    
    private func processReceivedData(_ data: Data) {
        // Notify raw data observers
        onDataReceived?(data)
        
        // Try to interpret as a text message
        if let message = String(data: data, encoding: .utf8) {
            // Check if this is a text message (starts with MSG:)
            if message.hasPrefix("MSG:") {
                let actualMessage = message.dropFirst(4) // Remove the MSG: prefix
                logger.debug("Received text message: \(actualMessage)")
                onMessageReceived?(String(actualMessage))
            }
            // If it starts with FILE:, it's a file transfer
            else if message.hasPrefix("FILE:") {
                // File handling would be implemented here
                logger.debug("Received file data")
            }
            // Otherwise just pass it through
            else {
                logger.debug("Received unformatted message: \(message)")
                onMessageReceived?(message)
            }
        }
    }
}

// MARK: - Convenience Extensions

public extension NetworkManager {
    /// Get the local IP address of the machine
    static func getLocalIPAddress() -> String? {
        var address: String?
        
        // Get list of all interfaces on the local machine
        var ifaddr: UnsafeMutablePointer<ifaddrs>?
        
        // Get ifaddr
        guard getifaddrs(&ifaddr) == 0 else { return nil }
        guard let firstAddr = ifaddr else { return nil }
        
        // For each interface ...
        for ptr in sequence(first: firstAddr, next: { $0.pointee.ifa_next }) {
            let interface = ptr.pointee
            
            // Check for IPv4 or IPv6 interface
            let addrFamily = interface.ifa_addr.pointee.sa_family
            if addrFamily == UInt8(AF_INET) || addrFamily == UInt8(AF_INET6) {
                
                // Check interface name (en0 is the primary interface on iOS devices)
                let name = String(cString: interface.ifa_name)
                if name == "en0" {
                    
                    // Convert interface address to a human readable string
                    var hostname = [CChar](repeating: 0, count: Int(NI_MAXHOST))
                    getnameinfo(interface.ifa_addr, socklen_t(interface.ifa_addr.pointee.sa_len),
                              &hostname, socklen_t(hostname.count),
                              nil, socklen_t(0), NI_NUMERICHOST)
                    address = String(cString: hostname)
                }
            }
        }
        
        freeifaddrs(ifaddr)
        return address
    }
    
    /// Get the public IP address using an external service
    static func getPublicIPAddress(completion: @escaping (String?) -> Void) {
        guard let url = URL(string: "https://api.ipify.org") else {
            completion(nil)
            return
        }
        
        let task = URLSession.shared.dataTask(with: url) { (data, response, error) in
            guard let data = data, error == nil else {
                completion(nil)
                return
            }
            
            let ipAddress = String(data: data, encoding: .utf8)
            completion(ipAddress)
        }
        
        task.resume()
    }
} 