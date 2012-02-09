"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from models import *

#
# Look more into the Django testing model and unittest2 on the python.org website. Django's test module is just a backport of unittest2.  
#
#class ParticleTest(TestCase):
#    def setUp(self):
#        self.u = UserData.get('test_user')
#        self.u2 = UserData.get('test_user2')
#        self.p = Particle.create('test particle', 'test', self.u, self.u, meta1=1, meta2={ 'foo' : 'bar'})
#
#    def test_core(self):
#        self.assertEqual(self.p, Particle.find_owned(self.u).first())
#        self.assertTrue(self.p.is_changeable_by(self.u))
#        self.assertFalse(self.p.is_changeable_by(self.u2))
#        self.p.add_administrator(self.u, self.u2)
#        self.assertTrue(self.p.is_changeable_by(self.u2))
#
#    def tearDown(self):
#        self.u.drop()
#        self.u2.drop()


