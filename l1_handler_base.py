# CloudShell L1 resource handler interface
#
# It should be unnecessary to edit this file.
#
# - All work for your L1 driver will be in a class that implements this interface
# - An instance of your implementation class will be passed as input to L1Driver

from abc import abstractmethod

from l1_driver_resource_info import L1DriverResourceInfo


class L1HandlerBase:
    @abstractmethod
    def login(self, address, username, password):
        """
        :param address: str
        :param username: str
        :param password: str
        :return: None
        """
        pass

    @abstractmethod
    def logout(self):
        """
        :return: None
        """
        pass

    @abstractmethod
    def get_resource_description(self, address):
        """
        :param address: str
        :return: L1DriverResourceInfo
        """
        if False:
            return L1DriverResourceInfo(None, None, None, None, None, -1)
        pass

    @abstractmethod
    def set_state_id(self, state_id):
        """
        :param state_id: str
        :return: None
        """
        pass

    @abstractmethod
    def get_state_id(self):
        """
        :return: str
        """
        pass

    @abstractmethod
    def map_bidi(self, src_port, dst_port, mapping_group_name):
        """
        :param src_port: str
        :param dst_port: str
        :param mapping_group_name: str
        :return: None
        """
        pass

    @abstractmethod
    def map_uni(self, src_port, dst_port):
        """
        :param src_port: str
        :param dst_port: str
        :return: None
        """
        pass

    @abstractmethod
    def map_clear(self, src_port, dst_port):
        """
        :param src_port: str
        :param dst_port: str
        :return: None
        """
        pass

    @abstractmethod
    def map_clear_to(self, src_port, dst_port):
        """
        :param src_port: str
        :param dst_port: str
        :return: None
        """
        pass

    @abstractmethod
    def get_attribute_value(self, address, attribute_name):
        """
        :param address: str
        :param attribute_name: str
        :return: str
        """
        pass

    @abstractmethod
    def set_speed_manual(self, src_port, dst_port, speed, duplex):
        """
        :param src_port: str
        :param dst_port: str
        :param speed: str
        :param duplex: str
        :return: None
        """
        pass
