from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: X-Authorization
configuration = swagger_client.Configuration()
configuration.api_key['X-Authorization'] = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ2aWN0b3J3Y21AZ21haWwuY29tIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJ1c2VySWQiOiIzMzgxMTQxMC0xNzJiLTExZTgtYmUyNS0wM2U5NDYxMTA5Y2EiLCJmaXJzdE5hbWUiOiJWaWN0b3IiLCJsYXN0TmFtZSI6Ik1lZGVpcm9zIiwiZW5hYmxlZCI6dHJ1ZSwiaXNQdWJsaWMiOmZhbHNlLCJ0ZW5hbnRJZCI6IjMzODBlZDAwLTE3MmItMTFlOC1iZTI1LTAzZTk0NjExMDljYSIsImN1c3RvbWVySWQiOiIxMzgxNDAwMC0xZGQyLTExYjItODA4MC04MDgwODA4MDgwODAiLCJpc3MiOiJ0aGluZ3Nib2FyZC5pbyIsImlhdCI6MTUyMjA2NTczMiwiZXhwIjoxNTMxMDY1NzMyfQ.9CkWocfpwgtuse2SB1TCenpnAVIyO6HVvqrqqACKOgOjTGz06sZIz7Sf7GnKNaeJOmaOf-L8Vu7R6GX8iuxDbA'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['X-Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = swagger_client.DeviceControllerApi(swagger_client.ApiClient(configuration))
device = swagger_client.Device() # Device | device

try: 
    # saveDevice
    api_response = api_instance.save_device_using_post(device)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DeviceControllerApi->save_device_using_post: %s\n" % e)
