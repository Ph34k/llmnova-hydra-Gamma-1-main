import pytest

from gamma_engine.core.messaging import Message, MessageBus, MessageType


def test_pub_sub_specific_type():
    bus = MessageBus()
    received = []
    
    def callback(msg):
        received.append(msg)
        
    bus.subscribe(MessageType.TEXT, callback)
    
    # Publish match
    msg1 = Message(type=MessageType.TEXT, content="hello")
    bus.publish(msg1)
    
    # Publish mismatch
    msg2 = Message(type=MessageType.ERROR, content="oops")
    bus.publish(msg2)
    
    assert len(received) == 1
    assert received[0].content == "hello"

def test_pub_sub_global():
    bus = MessageBus()
    received = []
    
    bus.subscribe(None, lambda m: received.append(m))
    
    bus.publish(Message(type=MessageType.TEXT, content="1"))
    bus.publish(Message(type=MessageType.ERROR, content="2"))
    
    assert len(received) == 2
