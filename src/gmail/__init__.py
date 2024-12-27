from . import server
import asyncio
import argparse

def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description='Gmail API MCP Server')
    parser.add_argument('--creds-file-path',
                        # required=True,
                       help='blah blah blah')
    parser.add_argument('--target-token-path',
                        # required=True,
                       help='blah blah blah')
    
    args = parser.parse_args()
    asyncio.run(server.main(args.creds_file_path, args.target_token_path))

# Optionally expose other important items at package level
__all__ = ['main', 'server']
