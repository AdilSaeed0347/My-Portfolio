#!/usr/bin/env python3
"""
Test script for Adil's Portfolio Server
Tests all endpoints and functionality
"""

import asyncio
import aiohttp
import json
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

class ServerTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_endpoint(self):
        """Test the health check endpoint"""
        logger.info("Testing health endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data['status']}")
                    return True
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    async def test_root_endpoint(self):
        """Test the root endpoint"""
        logger.info("Testing root endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Root endpoint working: {data['message']}")
                    return True
                else:
                    logger.error(f"❌ Root endpoint failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Root endpoint error: {e}")
            return False
    
    async def test_chat_health(self):
        """Test the chat health endpoint"""
        logger.info("Testing chat health endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/api/chat/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Chat health check passed: {data['status']}")
                    return True
                else:
                    logger.error(f"❌ Chat health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Chat health check error: {e}")
            return False
    
    async def test_chat_endpoint(self, message, language="en"):
        """Test the chat endpoint with a message"""
        logger.info(f"Testing chat with message: '{message}'")
        try:
            payload = {
                "message": message,
                "language": language,
                "session_id": "test_session"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Chat response received:")
                    logger.info(f"   Query Type: {data.get('query_type', 'unknown')}")
                    logger.info(f"   Response Length: {len(data.get('response', ''))}")
                    logger.info(f"   Processing Time: {data.get('processing_time', 0):.3f}s")
                    logger.info(f"   Sources: {len(data.get('sources', []))}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Chat failed ({response.status}): {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Chat error: {e}")
            return False
    
    async def test_chat_stats(self):
        """Test the chat stats endpoint"""
        logger.info("Testing chat stats endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/api/chat/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Chat stats received: {data['service']}")
                    return True
                else:
                    logger.error(f"❌ Chat stats failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Chat stats error: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        logger.info("🚀 Starting comprehensive server tests...")
        
        # Test basic endpoints
        tests = [
            ("Root Endpoint", self.test_root_endpoint()),
            ("Health Endpoint", self.test_health_endpoint()),
            ("Chat Health", self.test_chat_health()),
            ("Chat Stats", self.test_chat_stats()),
        ]
        
        # Test chat with various queries
        chat_tests = [
            ("About Query", self.test_chat_endpoint("Who is Adil Saeed?")),
            ("Projects Query", self.test_chat_endpoint("What projects has Adil worked on?")),
            ("Contact Query", self.test_chat_endpoint("How can I contact Adil?")),
            ("Education Query", self.test_chat_endpoint("Tell me about Adil's education")),
            ("Skills Query", self.test_chat_endpoint("What are Adil's technical skills?")),
            ("Math Query", self.test_chat_endpoint("What is 2+2?")),
            ("Urdu Query", self.test_chat_endpoint("Adil ke bare mein batao", "ur")),
        ]
        
        # Run basic tests
        passed = 0
        total = len(tests) + len(chat_tests)
        
        for test_name, test_coro in tests:
            logger.info(f"\n--- {test_name} ---")
            if await test_coro:
                passed += 1
            time.sleep(0.5)  # Small delay between tests
        
        # Run chat tests
        for test_name, test_coro in chat_tests:
            logger.info(f"\n--- {test_name} ---")
            if await test_coro:
                passed += 1
            time.sleep(1)  # Delay between chat tests
        
        # Results
        logger.info(f"\n🎯 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Your server is working perfectly!")
            return True
        else:
            logger.warning(f"⚠️  {total - passed} tests failed. Check the logs above.")
            return False

async def main():
    """Main test function"""
    logger.info("🧪 Starting Adil's Portfolio Server Tests...")
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status != 200:
                    logger.error("❌ Server is not responding!")
                    logger.info("Please start the server first with:")
                    logger.info("   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
                    return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to server: {e}")
        logger.info("Please start the server first with:")
        logger.info("   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
        return False
    
    # Run comprehensive tests
    async with ServerTester() as tester:
        success = await tester.run_comprehensive_test()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("\n✅ All tests completed successfully!")
        logger.info("Your portfolio chatbot is ready to use!")
        logger.info(f"Visit: {BASE_URL}/docs for API documentation")
    else:
        logger.error("\n❌ Some tests failed. Please check the issues above.")