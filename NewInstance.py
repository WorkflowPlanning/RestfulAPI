class NewInstance(object):
    def __init__(self, vm_type, vm_start, vm_end, pcp):
        self.vm_type = vm_type
        self.vm_start = vm_start
        self.vm_end = vm_end
        self.task_list = pcp
        self.cost = 0
