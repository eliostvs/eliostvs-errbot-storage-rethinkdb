from errbot import BotPlugin, botcmd


class MyClass(object):
    pass


class StorageTester(BotPlugin):
    """ This tests the storage backend.
    """

    @botcmd
    def teststorage(self, msg, args):
        for key in self:
            self.log.debug('Cleaning up %s' % key)
            del self[key]

        self.log.debug('test length')
        if len(self) != 0:
            return 'ERROR: it should be empty'

        self.log.debug('test set')
        self['foo'] = 'bar'
        if self['foo'] != 'bar':
            return 'ERROR: did not store foo'

        self.log.debug('test length 1')
        if len(self) != 1:
            return 'ERROR: Should be length 1'

        self.log.debug('test del')
        del self['foo']

        if len(self) != 0:
            return 'ERROR: Should be length 0'

        self.log.debug('test class serialization')
        self['clazz'] = MyClass()

        self.log.debug('test class deserialization')
        if type(self['clazz']) != MyClass:
            return 'ERROR: Should be type MyClass'

        try:
            self.log.debug('test missing key')
            self.log.debug(self['unknown'])
            return 'ERROR: should have send a KeyError'
        except KeyError:
            pass

        self.log.debug('test keys %s' % list(self.keys()))
        if list(self.keys())[0] != 'clazz' and len(self.keys()) != 1:
            return 'ERROR: key sets inconsistent'

        self.log.debug('everything is OK')
        return 'OK'
