from . import server
import asyncio
import argparse

def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='Theirstack API MCP Server')
    parser.add_argument('--api-config',
                        required=True,
                       help='File location to retrieve API configuration')
    
    args = parser.parse_args()
    asyncio.run(server.main( args.api_config))

# Optionally expose other important items at package level
__all__ = ['main', 'server']
