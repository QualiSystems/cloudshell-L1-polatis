# CloudShell L1 resource autoload XML helper
#
# It should be unnecessary to edit this file.
#
# - Generates the autoload XML resource format to return to CloudShell
# - Subresources are also represented with nested instances of this class
# - See example usage in <project>_l1_handler.py

class L1DriverResourceInfo:
    def __init__(self, name, full_address, family, model, map_path=None, serial='-1'):
        """
        :param name: str
        :param full_address: str
        :param family: str
        :param model: str
        :param map_path: str
        :param serial: str
        """
        self.name = name
        self.address = full_address
        self.family = family
        self.model = model
        self.serial = serial
        self.map_path = map_path
        self.subresources = []
        self.attrname2typevaluetuple = {}
        if False:
            self.subresources.append(L1DriverResourceInfo(None, None, None, None))

    def add_subresource(self, subresource):
        """
        :param subresource: L1DriverResourceInfo
        :return: None
        """
        self.subresources.append(subresource)

    def set_attribute(self, name, value, typename='String'):
        """
        :param name: str
        :param value: str
        :param typename: str
        :return: None
        """
        self.attrname2typevaluetuple[name] = (typename, value)

    def get_attribute(self, name):
        """
        :param name: str
        :return: str
        """
        return self.attrname2typevaluetuple[name][1]

    def to_string(self, tabs=''):
        """
        :param tabs: str
        :return: str
        """
        def indent(t, s):
            return t + (('\n' + t).join(s.split('\n'))).strip()

        return indent(tabs,
'''<ResourceInfo
        Name="''' + self.name + '''"
        Address="''' + self.address + '''"
        ResourceFamilyName="''' + self.family + '''"
        ResourceModelName="''' + self.model + '''"
        SerialNumber="''' + self.serial + '''"
>
    <ChildResources>''' + ('\n'.join(
                          [
                              x.to_string(tabs=tabs + '    ')
                              for x in self.subresources
                              ]
                      )) + '''
    </ChildResources>
    <ResourceAttributes>''' + (''.join(
                          [
                              '''
        <Attribute
            Name="''' + attrname + '''"
            Type="''' + self.attrname2typevaluetuple[attrname][0] + '''"
            Value="''' + str(self.attrname2typevaluetuple[attrname][1]) + '''"
        />'''
                              for attrname in self.attrname2typevaluetuple.keys()
                              ]
                      )) + '''
    </ResourceAttributes>''' + ('''
    <ResourceMapping><IncomingMapping>''' + self.map_path + '''</IncomingMapping></ResourceMapping>''' if self.map_path else ''
                                ) + '''
</ResourceInfo>
''')
