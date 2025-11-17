import asyncio
import logging
import os
import time
import unittest
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from apiGateway.ngrok import expose_file_via_ngrok, stop_ngrok_tunnel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestNgrokConnection(unittest.TestCase):

    def setUp(self):
        # Create a dummy file to expose
        self.dummy_file_path = os.path.join(os.path.dirname(__file__), "test_file.txt")
        with open(self.dummy_file_path, "w") as f:
            f.write("This is a test file for ngrok.")

    def tearDown(self):
        # Clean up the dummy file
        if os.path.exists(self.dummy_file_path):
            os.remove(self.dummy_file_path)

    def test_expose_file(self):
        """Tests the ngrok file exposure and connection."""
        logging.info("Starting test_expose_file...")

        def run_test():
            try:
                logging.info(f"Exposing file: {self.dummy_file_path}")
                public_url =  expose_file_via_ngrok(self.dummy_file_path)

                logging.info(f"Got public URL: {public_url}")
                self.assertIsNotNone(public_url)
                # self.assertTrue(public_url.startswith("http://"))
                time.sleep(90) # time to test the URL manually if needed


            except Exception as e:
                logging.error(f"An error occurred during the test: {e}", exc_info=True)
                self.fail(f"Test failed with exception: {e}")
            finally:
                logging.info("Stopping ngrok tunnel...")
                stop_ngrok_tunnel()
                logging.info("Ngrok tunnel stopped.")

        # Run the async test
        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
