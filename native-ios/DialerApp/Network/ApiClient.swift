// iOS Agent: URLSession Network Injector
import Foundation

class ApiClient {
    static let shared = ApiClient()
    let baseURL = "http://localhost:8000"
    var token: String?
    
    // Safely appending the JWT directly into Apple URLSession Headers
    func fetchLeads(completion: @escaping (Result<Data, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/api/mobile/leads"), let token = token else { return }
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error { completion(.failure(error)) }
            if let data = data { completion(.success(data)) }
        }.resume()
    }
}
