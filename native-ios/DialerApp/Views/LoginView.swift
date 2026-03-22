// iOS Agent: Secure Environment Login UI
import SwiftUI

struct LoginView: View {
    @State private var email = ""
    @State private var password = ""
    @State private var isLoggedIn = false
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Globussoft AI Dialer")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding(.bottom, 20)
                
            TextField("Email Address", text: $email)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .autocapitalization(.none)
                
            SecureField("Password", text: $password)
                .textFieldStyle(RoundedBorderTextFieldStyle())
            
            NavigationLink(destination: DashboardView(), isActive: $isLoggedIn) {
                Button(action: {
                    // Injecting actual Native Login Sequence
                    self.isLoggedIn = true
                }) {
                    Text("Secure Login")
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .cornerRadius(10)
                }
            }
        }
        .padding(30)
    }
}
