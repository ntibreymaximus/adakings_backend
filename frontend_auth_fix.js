// Frontend Authentication Fix
// Add this to your ViewOrdersPage.js or create a separate utility

// Enhanced error logging for debugging
const enhancedFetch = async (url, options = {}) => {
    console.log('🚀 Making API request:', {
        url,
        method: options.method || 'GET',
        headers: options.headers,
        hasToken: !!(options.headers && options.headers.Authorization)
    });

    try {
        const response = await fetch(url, options);
        
        console.log('📡 Response received:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries())
        });

        // Clone response to read body for logging
        const clonedResponse = response.clone();
        
        if (!response.ok) {
            let errorDetails;
            try {
                errorDetails = await clonedResponse.json();
            } catch {
                errorDetails = await clonedResponse.text();
            }
            
            console.error('❌ API Error:', {
                status: response.status,
                statusText: response.statusText,
                details: errorDetails,
                url
            });
        }

        return response;
    } catch (error) {
        console.error('🔥 Network Error:', {
            message: error.message,
            url,
            error
        });
        throw error;
    }
};

// Test function to verify authentication
const testAuthentication = async () => {
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.error('❌ No token found in localStorage');
        return;
    }

    console.log('🔑 Token found:', token.substring(0, 20) + '...');

    // Test 1: Check if token is expired
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expiry = new Date(payload.exp * 1000);
        console.log('⏰ Token expires at:', expiry);
        console.log('⏰ Current time:', new Date());
        console.log('✅ Token is', new Date() < expiry ? 'VALID' : 'EXPIRED');
    } catch (e) {
        console.error('❌ Invalid token format');
    }

    // Test 2: Make test request
    try {
        const response = await enhancedFetch('http://localhost:8000/api/orders/', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✅ API request successful!', data);
        }
    } catch (error) {
        console.error('❌ API request failed:', error);
    }
};

// Fix for ViewOrdersPage.js - Replace the fetch call in fetchOrders with:
/*
const response = await enhancedFetch(endpoint, {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Cache-Control': isToday ? 'max-age=60' : 'max-age=300'
    },
});
*/

// Export for use in browser console
window.testAuthentication = testAuthentication;
window.enhancedFetch = enhancedFetch;

console.log('🎯 Authentication testing functions loaded!');
console.log('Run testAuthentication() in console to debug');
