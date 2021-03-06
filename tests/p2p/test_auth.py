import asyncio

import pytest

from eth_utils import (
    decode_hex,
)

from eth_keys import keys

from p2p import ecies
from p2p import kademlia
from p2p.p2p_proto import Hello
from p2p.protocol import Protocol
from p2p.auth import (
    HandshakeInitiator,
    HandshakeResponder,
)
from p2p.peer import BasePeer


class DummyPeer(BasePeer):
    def process_sub_proto_handshake(self):
        pass

    def send_sub_proto_handshake(self):
        pass


@pytest.mark.asyncio
async def test_handshake():
    # This data comes from https://gist.github.com/fjl/3a78780d17c755d22df2
    test_values = {
        "initiator_private_key": "5e173f6ac3c669587538e7727cf19b782a4f2fda07c1eaa662c593e5e85e3051",
        "receiver_private_key": "c45f950382d542169ea207959ee0220ec1491755abe405cd7498d6b16adb6df8",
        "initiator_ephemeral_private_key": "19c2185f4f40634926ebed3af09070ca9e029f2edd5fae6253074896205f5f6c",  # noqa: E501
        "receiver_ephemeral_private_key": "d25688cf0ab10afa1a0e2dba7853ed5f1e5bf1c631757ed4e103b593ff3f5620",  # noqa: E501
        "auth_plaintext": "884c36f7ae6b406637c1f61b2f57e1d2cab813d24c6559aaf843c3f48962f32f46662c066d39669b7b2e3ba14781477417600e7728399278b1b5d801a519aa570034fdb5419558137e0d44cd13d319afe5629eeccb47fd9dfe55cc6089426e46cc762dd8a0636e07a54b31169eba0c7a20a1ac1ef68596f1f283b5c676bae4064abfcce24799d09f67e392632d3ffdc12e3d6430dcb0ea19c318343ffa7aae74d4cd26fecb93657d1cd9e9eaf4f8be720b56dd1d39f190c4e1c6b7ec66f077bb1100",  # noqa: E501
        "authresp_plaintext": "802b052f8b066640bba94a4fc39d63815c377fced6fcb84d27f791c9921ddf3e9bf0108e298f490812847109cbd778fae393e80323fd643209841a3b7f110397f37ec61d84cea03dcc5e8385db93248584e8af4b4d1c832d8c7453c0089687a700",  # noqa: E501
        "auth_ciphertext": "04a0274c5951e32132e7f088c9bdfdc76c9d91f0dc6078e848f8e3361193dbdc43b94351ea3d89e4ff33ddcefbc80070498824857f499656c4f79bbd97b6c51a514251d69fd1785ef8764bd1d262a883f780964cce6a14ff206daf1206aa073a2d35ce2697ebf3514225bef186631b2fd2316a4b7bcdefec8d75a1025ba2c5404a34e7795e1dd4bc01c6113ece07b0df13b69d3ba654a36e35e69ff9d482d88d2f0228e7d96fe11dccbb465a1831c7d4ad3a026924b182fc2bdfe016a6944312021da5cc459713b13b86a686cf34d6fe6615020e4acf26bf0d5b7579ba813e7723eb95b3cef9942f01a58bd61baee7c9bdd438956b426a4ffe238e61746a8c93d5e10680617c82e48d706ac4953f5e1c4c4f7d013c87d34a06626f498f34576dc017fdd3d581e83cfd26cf125b6d2bda1f1d56",  # noqa: E501
        "authresp_ciphertext": "049934a7b2d7f9af8fd9db941d9da281ac9381b5740e1f64f7092f3588d4f87f5ce55191a6653e5e80c1c5dd538169aa123e70dc6ffc5af1827e546c0e958e42dad355bcc1fcb9cdf2cf47ff524d2ad98cbf275e661bf4cf00960e74b5956b799771334f426df007350b46049adb21a6e78ab1408d5e6ccde6fb5e69f0f4c92bb9c725c02f99fa72b9cdc8dd53cff089e0e73317f61cc5abf6152513cb7d833f09d2851603919bf0fbe44d79a09245c6e8338eb502083dc84b846f2fee1cc310d2cc8b1b9334728f97220bb799376233e113",  # noqa: E501
        "ecdhe_shared_secret": "e3f407f83fc012470c26a93fdff534100f2c6f736439ce0ca90e9914f7d1c381",
        "initiator_nonce": "cd26fecb93657d1cd9e9eaf4f8be720b56dd1d39f190c4e1c6b7ec66f077bb11",
        "receiver_nonce": "f37ec61d84cea03dcc5e8385db93248584e8af4b4d1c832d8c7453c0089687a7",
        "aes_secret": "c0458fa97a5230830e05f4f20b7c755c1d4e54b1ce5cf43260bb191eef4e418d",
        "mac_secret": "48c938884d5067a1598272fcddaa4b833cd5e7d92e8228c0ecdfabbe68aef7f1",
        "token": "3f9ec2592d1554852b1f54d228f042ed0a9310ea86d038dc2b401ba8cd7fdac4",
        "initial_egress_MAC": "09771e93b1a6109e97074cbe2d2b0cf3d3878efafe68f53c41bb60c0ec49097e",
        "initial_ingress_MAC": "75823d96e23136c89666ee025fb21a432be906512b3dd4a3049e898adb433847",
        "initiator_hello_packet": "6ef23fcf1cec7312df623f9ae701e63b550cdb8517fefd8dd398fc2acd1d935e6e0434a2b96769078477637347b7b01924fff9ff1c06df2f804df3b0402bbb9f87365b3c6856b45e1e2b6470986813c3816a71bff9d69dd297a5dbd935ab578f6e5d7e93e4506a44f307c332d95e8a4b102585fd8ef9fc9e3e055537a5cec2e9",  # noqa: E501
        "receiver_hello_packet": "6ef23fcf1cec7312df623f9ae701e63be36a1cdd1b19179146019984f3625d4a6e0434a2b96769050577657247b7b02bc6c314470eca7e3ef650b98c83e9d7dd4830b3f718ff562349aead2530a8d28a8484604f92e5fced2c6183f304344ab0e7c301a0c05559f4c25db65e36820b4b909a226171a60ac6cb7beea09376d6d8"  # noqa: E501
    }
    for k, v in test_values.items():
        test_values[k] = decode_hex(v)

    initiator_remote = kademlia.Node(
        keys.PrivateKey(test_values['receiver_private_key']).public_key,
        kademlia.Address('0.0.0.0', 0, 0))
    initiator = HandshakeInitiator(
        initiator_remote,
        keys.PrivateKey(test_values['initiator_private_key']))
    initiator.ephemeral_privkey = keys.PrivateKey(test_values['initiator_ephemeral_private_key'])

    responder_remote = kademlia.Node(
        keys.PrivateKey(test_values['initiator_private_key']).public_key,
        kademlia.Address('0.0.0.0', 0, 0))
    responder = HandshakeResponder(
        responder_remote,
        keys.PrivateKey(test_values['receiver_private_key']))
    responder.ephemeral_privkey = keys.PrivateKey(test_values['receiver_ephemeral_private_key'])

    # Check that the auth message generated by the initiator is what we expect. Notice that we
    # can't use the auth_init generated here because the non-deterministic prefix would cause the
    # derived secrets to not match the expected values.
    _auth_init = initiator.create_auth_message(test_values['initiator_nonce'])
    assert len(_auth_init) == len(test_values['auth_plaintext'])
    assert _auth_init[65:] == test_values['auth_plaintext'][65:]  # starts with non deterministic k

    # Check that encrypting and decrypting the auth_init gets us the orig msg.
    _auth_init_ciphertext = initiator.encrypt_auth_message(_auth_init)
    assert _auth_init == ecies.decrypt(_auth_init_ciphertext, responder.privkey)

    # Check that the responder correctly decodes the auth msg.
    auth_msg_ciphertext = test_values['auth_ciphertext']
    initiator_ephemeral_pubkey, initiator_nonce = responder.decode_authentication(
        auth_msg_ciphertext)
    assert initiator_nonce == test_values['initiator_nonce']
    assert initiator_ephemeral_pubkey == (
        keys.PrivateKey(test_values['initiator_ephemeral_private_key']).public_key)

    # Check that the auth_ack msg generated by the responder is what we expect.
    auth_ack_msg = responder.create_auth_ack_message(test_values['receiver_nonce'])
    assert auth_ack_msg == test_values['authresp_plaintext']

    # Check that the secrets derived from ephemeral key agreements match the expected values.
    auth_ack_ciphertext = test_values['authresp_ciphertext']
    aes_secret, mac_secret, egress_mac, ingress_mac = responder.derive_secrets(
        initiator_nonce, test_values['receiver_nonce'],
        initiator_ephemeral_pubkey, auth_msg_ciphertext, auth_ack_ciphertext)
    assert aes_secret == test_values['aes_secret']
    assert mac_secret == test_values['mac_secret']
    # Test values are from initiator perspective, so they're reversed here.
    assert ingress_mac.digest() == test_values['initial_egress_MAC']
    assert egress_mac.digest() == test_values['initial_ingress_MAC']

    # Check that the initiator secrets match as well.
    responder_ephemeral_pubkey, responder_nonce = initiator.decode_auth_ack_message(
        test_values['authresp_ciphertext'])
    (initiator_aes_secret,
     initiator_mac_secret,
     initiator_egress_mac,
     initiator_ingress_mac) = initiator.derive_secrets(
         initiator_nonce, responder_nonce,
         responder_ephemeral_pubkey, auth_msg_ciphertext, auth_ack_ciphertext)
    assert initiator_aes_secret == aes_secret
    assert initiator_mac_secret == mac_secret
    assert initiator_ingress_mac.digest() == test_values['initial_ingress_MAC']
    assert initiator_egress_mac.digest() == test_values['initial_egress_MAC']

    # Finally, check that two Peers configured with the secrets generated above understand each
    # other.
    responder_reader = asyncio.StreamReader()
    initiator_reader = asyncio.StreamReader()
    # Link the initiator's writer to the responder's reader, and the responder's writer to the
    # initiator's reader.
    responder_writer = type(
        "mock-streamwriter",
        (object,),
        {"write": initiator_reader.feed_data}
    )
    initiator_writer = type(
        "mock-streamwriter",
        (object,),
        {"write": responder_reader.feed_data}
    )
    initiator_peer = DummyPeer(
        remote=initiator.remote, privkey=initiator.privkey, reader=initiator_reader,
        writer=initiator_writer, aes_secret=initiator_aes_secret, mac_secret=initiator_mac_secret,
        egress_mac=initiator_egress_mac, ingress_mac=initiator_ingress_mac, chaindb=None,
        network_id=1)
    initiator_peer.base_protocol.send_handshake()
    responder_peer = DummyPeer(
        remote=responder.remote, privkey=responder.privkey, reader=responder_reader,
        writer=responder_writer, aes_secret=aes_secret, mac_secret=mac_secret,
        egress_mac=egress_mac, ingress_mac=ingress_mac, chaindb=None, network_id=1)
    responder_peer.base_protocol.send_handshake()

    # The handshake msgs sent by each peer (above) are going to be fed directly into their remote's
    # reader, and thus the read_msg() calls will return immediately.
    responder_hello, _ = await responder_peer.read_msg()
    initiator_hello, _ = await initiator_peer.read_msg()

    assert isinstance(responder_hello, Hello)
    assert isinstance(initiator_hello, Hello)


def test_handshake_eip8():
    # Data taken from https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8.md
    test_values = {
        "initiator_private_key": "49a7b37aa6f6645917e7b807e9d1c00d4fa71f18343b0d4122a4d2df64dd6fee",
        "receiver_private_key": "b71c71a67e1177ad4e901695e1b4b9ee17ae16c6668d313eac2f96dbcda3f291",
        "initiator_ephemeral_private_key":
            "869d6ecf5211f1cc60418a13b9d870b22959d0c16f02bec714c960dd2298a32d",
        "receiver_ephemeral_private_key":
            "e238eb8e04fee6511ab04c6dd3c89ce097b11f25d584863ac2b6d5b35b1847e4",
        "initiator_nonce": "7e968bba13b6c50e2c4cd7f241cc0d64d1ac25c7f5952df231ac6a2bda8ee5d6",
        "receiver_nonce": "559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd",
    }
    for k, v in test_values.items():
        test_values[k] = decode_hex(v)

    initiator_remote = kademlia.Node(
        keys.PrivateKey(test_values['receiver_private_key']).public_key,
        kademlia.Address('0.0.0.0', 0, 0))
    initiator = HandshakeInitiator(
        initiator_remote,
        keys.PrivateKey(test_values['initiator_private_key']))
    initiator.ephemeral_privkey = keys.PrivateKey(test_values['initiator_ephemeral_private_key'])

    responder_remote = kademlia.Node(
        keys.PrivateKey(test_values['initiator_private_key']).public_key,
        kademlia.Address('0.0.0.0', 0, 0))
    responder = HandshakeResponder(
        responder_remote,
        keys.PrivateKey(test_values['receiver_private_key']))
    responder.ephemeral_privkey = keys.PrivateKey(test_values['receiver_ephemeral_private_key'])

    auth_init_ciphertext = decode_hex(
        "01b304ab7578555167be8154d5cc456f567d5ba302662433674222360f08d5f1534499d3678b513b"
        "0fca474f3a514b18e75683032eb63fccb16c156dc6eb2c0b1593f0d84ac74f6e475f1b8d56116b84"
        "9634a8c458705bf83a626ea0384d4d7341aae591fae42ce6bd5c850bfe0b999a694a49bbbaf3ef6c"
        "da61110601d3b4c02ab6c30437257a6e0117792631a4b47c1d52fc0f8f89caadeb7d02770bf999cc"
        "147d2df3b62e1ffb2c9d8c125a3984865356266bca11ce7d3a688663a51d82defaa8aad69da39ab6"
        "d5470e81ec5f2a7a47fb865ff7cca21516f9299a07b1bc63ba56c7a1a892112841ca44b6e0034dee"
        "70c9adabc15d76a54f443593fafdc3b27af8059703f88928e199cb122362a4b35f62386da7caad09"
        "c001edaeb5f8a06d2b26fb6cb93c52a9fca51853b68193916982358fe1e5369e249875bb8d0d0ec3"
        "6f917bc5e1eafd5896d46bd61ff23f1a863a8a8dcd54c7b109b771c8e61ec9c8908c733c0263440e"
        "2aa067241aaa433f0bb053c7b31a838504b148f570c0ad62837129e547678c5190341e4f1693956c"
        "3bf7678318e2d5b5340c9e488eefea198576344afbdf66db5f51204a6961a63ce072c8926c")

    # Check that we can decrypt/decode the EIP-8 auth init message.
    initiator_ephemeral_pubkey, initiator_nonce = responder.decode_authentication(
        auth_init_ciphertext)
    assert initiator_nonce == test_values['initiator_nonce']
    assert initiator_ephemeral_pubkey == (
        keys.PrivateKey(test_values['initiator_ephemeral_private_key']).public_key)

    responder_nonce = test_values['receiver_nonce']
    auth_ack_ciphertext = decode_hex(
        "01ea0451958701280a56482929d3b0757da8f7fbe5286784beead59d95089c217c9b917788989470"
        "b0e330cc6e4fb383c0340ed85fab836ec9fb8a49672712aeabbdfd1e837c1ff4cace34311cd7f4de"
        "05d59279e3524ab26ef753a0095637ac88f2b499b9914b5f64e143eae548a1066e14cd2f4bd7f814"
        "c4652f11b254f8a2d0191e2f5546fae6055694aed14d906df79ad3b407d94692694e259191cde171"
        "ad542fc588fa2b7333313d82a9f887332f1dfc36cea03f831cb9a23fea05b33deb999e85489e645f"
        "6aab1872475d488d7bd6c7c120caf28dbfc5d6833888155ed69d34dbdc39c1f299be1057810f34fb"
        "e754d021bfca14dc989753d61c413d261934e1a9c67ee060a25eefb54e81a4d14baff922180c395d"
        "3f998d70f46f6b58306f969627ae364497e73fc27f6d17ae45a413d322cb8814276be6ddd13b885b"
        "201b943213656cde498fa0e9ddc8e0b8f8a53824fbd82254f3e2c17e8eaea009c38b4aa0a3f306e8"
        "797db43c25d68e86f262e564086f59a2fc60511c42abfb3057c247a8a8fe4fb3ccbadde17514b7ac"
        "8000cdb6a912778426260c47f38919a91f25f4b5ffb455d6aaaf150f7e5529c100ce62d6d92826a7"
        "1778d809bdf60232ae21ce8a437eca8223f45ac37f6487452ce626f549b3b5fdee26afd2072e4bc7"
        "5833c2464c805246155289f4")
    aes_secret, mac_secret, _, _ = responder.derive_secrets(
        initiator_nonce, responder_nonce, initiator_ephemeral_pubkey, auth_init_ciphertext,
        auth_ack_ciphertext)

    # Check that the secrets derived by the responder match the expected values.
    expected_aes_secret = decode_hex(
        "80e8632c05fed6fc2a13b0f8d31a3cf645366239170ea067065aba8e28bac487")
    expected_mac_secret = decode_hex(
        "2ea74ec5dae199227dff1af715362700e989d889d7a493cb0639691efb8e5f98")
    assert aes_secret == expected_aes_secret
    assert mac_secret == expected_mac_secret

    responder_ephemeral_pubkey, responder_nonce = initiator.decode_auth_ack_message(
        auth_ack_ciphertext)
    initiator_aes_secret, initiator_mac_secret, _, _ = initiator.derive_secrets(
        initiator_nonce, responder_nonce, responder_ephemeral_pubkey, auth_init_ciphertext,
        auth_ack_ciphertext)

    # Check that the secrets derived by the initiator match the expected values.
    assert initiator_aes_secret == expected_aes_secret
    assert initiator_mac_secret == expected_mac_secret


def test_eip8_hello():
    # Data taken from https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8.md
    payload = decode_hex(
        "f87137916b6e6574682f76302e39312f706c616e39cdc5836574683dc6846d6f726b1682270fb840"
        "fda1cff674c90c9a197539fe3dfb53086ace64f83ed7c6eabec741f7f381cc803e52ab2cd55d5569"
        "bce4347107a310dfd5f88a010cd2ffd1005ca406f1842877c883666f6f836261720304")
    dummy_proto = Protocol(peer=None, cmd_id_offset=0)
    Hello(dummy_proto).decode_payload(payload)
