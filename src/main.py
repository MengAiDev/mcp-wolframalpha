import httpx
import xml.etree.ElementTree as ET
from mcp.server.fastmcp import FastMCP
from mcp.error import ConfigurationError, InternalError, ApiError
from mcp.decorators import validate_params

app = FastMCP("mcp-wolframalpha")
app.configure_from_env("WOLFRAM_ALPHA_APPID")


async def wolfram_alpha_query(query: str, appid: str):
    if not appid:
        raise ConfigurationError("Missing Wolfram Alpha APPID")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            url = "https://api.wolframalpha.com/v2/query"
            params = {
                "input": query,
                "format": "plaintext",
                "output": "json",
                "appid": appid
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            xml_response = ET.fromstring(response.content)
            pod = xml_response.find(".//pod")
            if pod is not None:
                plaintext = pod.find("plaintext")
                if plaintext is not None:
                    return {"result": plaintext.text}
            return {"result": "No result found"}
    except (httpx.HTTPError, ET.ParseError, TimeoutError) as e:
        raise InternalError(str(e))


@validate_params(query=str)
@app.tool
async def get_wolfram_alpha_result(query: str):
    """
    Get the result of a query from Wolfram Alpha.
    """
    try:
        appid = app.config["WOLFRAM_ALPHA_APPID"]
        return await wolfram_alpha_query(query, appid)
    except Exception as e:
        raise ApiError(str(e))


if __name__ == "__main__":
    app.run(transport="stdio")