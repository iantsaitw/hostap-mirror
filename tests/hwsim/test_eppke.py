# Test cases for Enhanced Privacy Protection Key Exchange(EPPKE)
# Copyright (c) 2025, Qualcomm Innovation Center, Inc.
#
# This software may be distributed under the terms of the BSD license.
# See README for more details.

import time

import hostapd
from wpasupplicant import WpaSupplicant
from utils import *
from hwsim import HWSimRadio
from test_eht import eht_mld_ap_wpa2_params, eht_mld_enable_ap, traffic_test, eht_verify_status

def test_eppke_akm_suite_and_rsnxe_feature_flags(dev, apdev):
    """AP EPPKE AKM Advertisement with SAE base AKM and EPPKE related feature flags"""
    ssid = "test-eppke-authentication"
    params = hostapd.wpa3_params(ssid=ssid,
                                 password = "1234567890")
    params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
    params['assoc_frame_encryption'] = '1'
    params['pmksa_caching_privacy'] = '1'
    params['eap_using_authentication_frames'] = '1'
    params['sae_pwe'] = '2'

    hapd = hostapd.add_ap(apdev[0], params)
    time.sleep(2)
    #TODO: Add pcap file checks to validate correct
    #RSNXE bits and AKM suite presence in Beacon frames

    #Disable all EPPKE related RSNXE flags and test
    params['assoc_frame_encryption'] = '0'
    params['pmksa_caching_privacy'] = '0'
    params['eap_using_authentication_frames'] = '0'
    hapd = hostapd.add_ap(apdev[0], params)
    time.sleep(2)

def test_eppke_ap_with_base_akm_sae_legacy_client(dev, apdev):
    """EPPKE authentication with a Non-MLO AP with base AKM SAE and legacy client"""
    ssid = "test-eppke-authentication"
    passphrase = '1234567890'
    params = hostapd.wpa3_params(ssid=ssid,
				 password = passphrase)
    params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
    params['assoc_frame_encryption'] = '1'
    params['pmksa_caching_privacy'] = '1'
    params['eap_using_authentication_frames'] = '1'
    params['sae_pwe'] = '2'
    hapd = hostapd.add_ap(apdev[0], params)

    try:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "1")
        dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                       key_mgmt="SAE", ieee80211w="2", beacon_prot="1",
                       pairwise="CCMP")
        hapd.wait_sta();
        sta = hapd.get_sta(dev[0].own_addr())
        if sta["AKMSuiteSelector"] != '00-0f-ac-8' or sta["auth_alg"] != '9':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")

    finally:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "0")

def run_eppke_sae_ext_key(dev, apdev, group):
    """EPPKE authentication with a Non-MLO AP with base AKM SAE-EXT-KEY and legacy client"""
    ssid = "test-eppke-authentication"
    passphrase = '1234567890'
    params = hostapd.wpa3_params(ssid=ssid,
				 password = passphrase)
    params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'SAE-EXT-KEY EPPKE'
    params['assoc_frame_encryption'] = '1'
    params['pmksa_caching_privacy'] = '1'
    params['eap_using_authentication_frames'] = '1'
    params['sae_pwe'] = '2'
    params['pasn_groups'] = str(group)
    params['sae_groups'] = str(group)
    hapd = hostapd.add_ap(apdev[0], params)

    try:
        dev[0].set("sae_groups", str(group))
        dev[0].set("sae_pwe", "1")
        dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                       key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                       pairwise="CCMP")
        hapd.wait_sta();
        sta = hapd.get_sta(dev[0].own_addr())
        if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")

    finally:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "0")

def test_eppke_ap_with_base_akm_sae_ext_legacy_client_19(dev, apdev):
    """EPPKE authentication with a Non-MLO AP with base AKM SAE-EXT-KEY and legacy client, group 19"""
    run_eppke_sae_ext_key(dev, apdev, 19)

def test_eppke_ap_with_base_akm_sae_ext_legacy_client_20(dev, apdev):
    """EPPKE authentication with a Non-MLO AP with base AKM SAE-EXT-KEY and legacy client, group 20"""
    run_eppke_sae_ext_key(dev, apdev, 20)

def test_eppke_ap_with_base_akm_sae_ext_legacy_client_21(dev, apdev):
    """EPPKE authentication with a Non-MLO AP with base AKM SAE-EXT-KEY and legacy client, group 21"""
    run_eppke_sae_ext_key(dev, apdev, 21)

def test_eppke_mld_ap_with_base_akm_sae_legacy_client(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE and legacy client"""
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface):
        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt="SAE", mfp="2", pwe='1')
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"

        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        params['channel'] = '6'
        hapd1 = eht_mld_enable_ap(hapd_iface, 1, params)

        try:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "1")
            dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                           key_mgmt="SAE", ieee80211w="2", beacon_prot="1",
                           pairwise="CCMP GCMP-256")
            bssid = dev[0].get_status_field("bssid")
            if hapd0.own_addr() == bssid:
                hapd0.wait_sta();
                sta = hapd0.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-8' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            elif hapd1.own_addr() == bssid:
                hapd1.wait_sta();
                sta = hapd1.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-8' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            else:
                raise Exception("Unknown BSSID: " + bssid)
        finally:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "0")

def test_eppke_mld_ap_with_base_akm_sae_ext_legacy_client(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE-EXT and legacy client"""
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface):
        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt="SAE-EXT-KEY", mfp="2", pwe='1')
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        params['channel'] = '6'
        hapd1 = eht_mld_enable_ap(hapd_iface, 1, params)

        try:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "1")
            dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                           key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                           pairwise="CCMP GCMP-256")
            bssid = dev[0].get_status_field("bssid")
            if hapd0.own_addr() == bssid:
                hapd0.wait_sta();
                sta = hapd0.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            elif hapd1.own_addr() == bssid:
                hapd1.wait_sta();
                sta = hapd1.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            else:
                raise Exception("Unknown BSSID: " + bssid)
        finally:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "0")

def run_eppke_mld_two_links(dev, apdev, key_mgmt):
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface), \
        HWSimRadio(use_mlo=True) as (wpas_radio, wpas_iface):

        wpas = WpaSupplicant(global_iface='/tmp/wpas-wlan5')
        wpas.interface_add(wpas_iface)

        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt=key_mgmt, mfp="2", pwe='1',
                                        beacon_prot=1)
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        params['channel'] = '6'
        hapd1 = eht_mld_enable_ap(hapd_iface, 1, params)

        wpas.set("sae_groups", "")
        wpas.set("sae_pwe", "1")
        wpas.connect(ssid, sae_password=passphrase, scan_freq="2412 2437",
                     key_mgmt=key_mgmt, ieee80211w="2", beacon_prot="1",
                     pairwise="CCMP GCMP-256")
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=3, active_links=3)

def run_eppke_mld_one_link(dev, apdev, key_mgmt):
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface), \
        HWSimRadio(use_mlo=True) as (wpas_radio, wpas_iface):

        wpas = WpaSupplicant(global_iface='/tmp/wpas-wlan5')
        wpas.interface_add(wpas_iface)

        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt=key_mgmt, mfp="2", pwe='1',
                                        beacon_prot=1)
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        wpas.set("sae_groups", "")
        wpas.set("sae_pwe", "1")
        wpas.connect(ssid, sae_password=passphrase, scan_freq="2412",
                     key_mgmt=key_mgmt, ieee80211w="2", beacon_prot="1",
                     pairwise="CCMP GCMP-256")
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=1, active_links=1)

def test_eppke_with_base_akm_sae_single_link(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE and MLD client using single link"""
    run_eppke_mld_one_link(dev, apdev, key_mgmt="SAE")

def test_eppke_with_base_akm_sae_ext_single_link(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE-EXT and MLD client using single link"""
    run_eppke_mld_one_link(dev, apdev, key_mgmt="SAE-EXT-KEY")

def test_eppke_with_base_akm_sae_two_link(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE and MLD client using two links"""
    run_eppke_mld_two_links(dev, apdev, key_mgmt="SAE")

def test_eppke_with_base_akm_sae_ext_two_link(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE-EXT and MLD client using two links"""
    run_eppke_mld_two_links(dev, apdev, key_mgmt="SAE-EXT-KEY")

def test_eppke_ap_with_base_akm_sae_legacy_client_pmksa_cached(dev, apdev):
    """EPPKE authentication with a Non-MLO AP with base AKM SAE and legacy client with PMKSA Caching"""
    ssid = "test-eppke-authentication"
    passphrase = '1234567890'
    params = hostapd.wpa3_params(ssid=ssid,
            password = passphrase)
    params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
    params['assoc_frame_encryption'] = '1'
    params['pmksa_caching_privacy'] = '1'
    params['eap_using_authentication_frames'] = '1'
    params['sae_pwe'] = '2'
    hapd = hostapd.add_ap(apdev[0], params)

    try:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "1")
        dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                key_mgmt="SAE", ieee80211w="2", beacon_prot="1",
                pairwise="CCMP")
        hapd.wait_sta();
        sta = hapd.get_sta(dev[0].own_addr())
        if sta["AKMSuiteSelector"] != '00-0f-ac-8' or sta["auth_alg"] != '9':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")

        dev[0].request("DISCONNECT")
        dev[0].wait_disconnected()
        dev[0].request("RECONNECT")
        dev[0].wait_connected(timeout=15, error="Reconnect timed out")
        val = dev[0].get_status_field('sae_group')
        if val is not None:
            raise Exception("SAE group claimed to have been used: " + val)
        sta = hapd.get_sta(dev[0].own_addr())
        if sta['auth_alg'] != '9' or sta['AKMSuiteSelector'] != '00-0f-ac-8':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value after PMKSA caching")

    finally:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "0")

def test_eppke_ap_with_base_akm_sae_ext_legacy_client_pmksa_cached(dev, apdev):
    """EPPKE authentication with a Non-MLO AP with base AKM SAE-EXT-KEY and legacy client"""
    ssid = "test-eppke-authentication"
    passphrase = '1234567890'
    params = hostapd.wpa3_params(ssid=ssid,
				 password = passphrase)
    params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'SAE-EXT-KEY EPPKE'
    params['assoc_frame_encryption'] = '1'
    params['pmksa_caching_privacy'] = '1'
    params['eap_using_authentication_frames'] = '1'
    params['sae_pwe'] = '2'
    hapd = hostapd.add_ap(apdev[0], params)

    try:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "1")
        dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                       key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                       pairwise="CCMP")
        hapd.wait_sta();
        sta = hapd.get_sta(dev[0].own_addr())
        if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")

        dev[0].request("DISCONNECT")
        dev[0].wait_disconnected()
        dev[0].request("RECONNECT")
        dev[0].wait_connected(timeout=15, error="Reconnect timed out")
        val = dev[0].get_status_field('sae_group')
        if val is not None:
            raise Exception("SAE group claimed to have been used: " + val)
        sta = hapd.get_sta(dev[0].own_addr())
        if sta['auth_alg'] != '9' or sta['AKMSuiteSelector'] != '00-0f-ac-24':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value after PMKSA caching")

    finally:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "0")

def test_eppke_mld_ap_with_base_akm_sae_legacy_client_pmksa_cached(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE and legacy client"""
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface):
        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt="SAE", mfp="2", pwe='1')
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"

        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        params['channel'] = '6'
        hapd1 = eht_mld_enable_ap(hapd_iface, 1, params)

        try:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "1")
            dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                           key_mgmt="SAE", ieee80211w="2", beacon_prot="1",
                           pairwise="CCMP GCMP-256")
            bssid = dev[0].get_status_field("bssid")
            if hapd0.own_addr() == bssid:
                hapd0.wait_sta();
                sta = hapd0.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-8' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            elif hapd1.own_addr() == bssid:
                hapd1.wait_sta();
                sta = hapd1.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-8' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            else:
                raise Exception("Unknown BSSID: " + bssid)

            dev[0].request("DISCONNECT")
            dev[0].wait_disconnected()
            dev[0].request("RECONNECT")
            dev[0].wait_connected(timeout=15, error="Reconnect timed out")
            val = dev[0].get_status_field('sae_group')
            if val is not None:
                raise Exception("SAE group claimed to have been used: " + val)

            bssid = dev[0].get_status_field("bssid")
            if hapd0.own_addr() == bssid:
                hapd0.wait_sta();
                sta = hapd0.get_sta(dev[0].own_addr())
            elif hapd1.own_addr() == bssid:
                hapd1.wait_sta();
                sta = hapd1.get_sta(dev[0].own_addr())
            else:
                raise Exception("Unknown BSSID: " + bssid)

            if sta['auth_alg'] != '9' or sta['AKMSuiteSelector'] != '00-0f-ac-8':
                raise Exception("Incorrect Auth Algo/AKMSuiteSelector value after PMKSA caching")

        finally:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "0")

def test_eppke_mld_ap_with_base_akm_sae_ext_legacy_client_pmksa_cached(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE-EXT and legacy client"""
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface):
        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt="SAE-EXT-KEY", mfp="2", pwe='1')
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        params['channel'] = '6'
        hapd1 = eht_mld_enable_ap(hapd_iface, 1, params)

        try:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "1")
            dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                           key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                           pairwise="CCMP GCMP-256")
            bssid = dev[0].get_status_field("bssid")
            if hapd0.own_addr() == bssid:
                hapd0.wait_sta();
                sta = hapd0.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            elif hapd1.own_addr() == bssid:
                hapd1.wait_sta();
                sta = hapd1.get_sta(dev[0].own_addr())
                if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
                    raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")
            else:
                raise Exception("Unknown BSSID: " + bssid)

            dev[0].request("DISCONNECT")
            dev[0].wait_disconnected()
            dev[0].request("RECONNECT")
            dev[0].wait_connected(timeout=15, error="Reconnect timed out")
            val = dev[0].get_status_field('sae_group')
            if val is not None:
                raise Exception("SAE group claimed to have been used: " + val)

            bssid = dev[0].get_status_field("bssid")
            if hapd0.own_addr() == bssid:
                hapd0.wait_sta();
                sta = hapd0.get_sta(dev[0].own_addr())
            elif hapd1.own_addr() == bssid:
                hapd1.wait_sta();
                sta = hapd1.get_sta(dev[0].own_addr())
            else:
                raise Exception("Unknown BSSID: " + bssid)

            if sta['auth_alg'] != '9' or sta['AKMSuiteSelector'] != '00-0f-ac-24':
                raise Exception("Incorrect Auth Algo/AKMSuiteSelector value after PMKSA caching")

        finally:
            dev[0].set("sae_groups", "")
            dev[0].set("sae_pwe", "0")

def run_eppke_mld_one_link_pmksa_cached(dev, apdev, key_mgmt):
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface), \
        HWSimRadio(use_mlo=True) as (wpas_radio, wpas_iface):

        wpas = WpaSupplicant(global_iface='/tmp/wpas-wlan5')
        wpas.interface_add(wpas_iface)

        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt=key_mgmt, mfp="2", pwe='1',
                                        beacon_prot=1)
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        wpas.set("sae_groups", "")
        wpas.set("sae_pwe", "1")
        wpas.connect(ssid, sae_password=passphrase, scan_freq="2412",
                     key_mgmt=key_mgmt, ieee80211w="2", beacon_prot="1",
                     pairwise="CCMP GCMP-256")
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=1, active_links=1)

        wpas.request("DISCONNECT")
        wpas.wait_disconnected()
        wpas.request("RECONNECT")
        wpas.wait_connected(timeout=15, error="Reconnect timed out")
        val = wpas.get_status_field('sae_group')
        if val is not None:
            raise Exception("SAE group claimed to have been used: " + val)
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=1, active_links=1)

def test_eppke_with_base_akm_sae_single_link_pmksa_cached(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE and MLD client using single link"""
    run_eppke_mld_one_link_pmksa_cached(dev, apdev, key_mgmt="SAE")

def test_eppke_with_base_akm_sae_ext_single_link_pmksa_cached(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE-EXT and MLD client using single link"""
    run_eppke_mld_one_link_pmksa_cached(dev, apdev, key_mgmt="SAE-EXT-KEY")

def run_eppke_mld_two_links_pmksa_cached(dev, apdev, key_mgmt):
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface), \
        HWSimRadio(use_mlo=True) as (wpas_radio, wpas_iface):

        wpas = WpaSupplicant(global_iface='/tmp/wpas-wlan5')
        wpas.interface_add(wpas_iface)

        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt=key_mgmt, mfp="2", pwe='1',
                                        beacon_prot=1)
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        params['channel'] = '6'
        hapd1 = eht_mld_enable_ap(hapd_iface, 1, params)

        wpas.set("sae_groups", "")
        wpas.set("sae_pwe", "1")
        wpas.connect(ssid, sae_password=passphrase, scan_freq="2412 2437",
                     key_mgmt=key_mgmt, ieee80211w="2", beacon_prot="1",
                     pairwise="CCMP GCMP-256")
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=3, active_links=3)

        wpas.request("DISCONNECT")
        wpas.wait_disconnected()
        wpas.request("RECONNECT")
        wpas.wait_connected(timeout=15, error="Reconnect timed out")
        val = wpas.get_status_field('sae_group')
        if val is not None:
            raise Exception("SAE group claimed to have been used: " + val)
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=3, active_links=3)

def test_eppke_with_base_akm_sae_two_link_pmksa_cached(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE and MLD client using two links"""
    run_eppke_mld_two_links_pmksa_cached(dev, apdev, key_mgmt="SAE")

def test_eppke_with_base_akm_sae_ext_two_link_pmksa_cached(dev, apdev):
    """EPPKE authentication with an MLD AP with base AKM SAE-EXT and MLD client using two links"""
    run_eppke_mld_two_links_pmksa_cached(dev, apdev, key_mgmt="SAE-EXT-KEY")

def test_eppke_ap_gtk_rekey_with_base_akm_sae_ext_legacy_client(dev, apdev):
    """EPPKE AP and GTK rekey"""
    ssid = "test-eppke-authentication"
    passphrase = '1234567890'
    params = hostapd.wpa3_params(ssid=ssid,
				 password = passphrase)
    params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'SAE-EXT-KEY EPPKE'
    params['assoc_frame_encryption'] = '1'
    params['pmksa_caching_privacy'] = '1'
    params['eap_using_authentication_frames'] = '1'
    params['sae_pwe'] = '2'
    params['wpa_group_rekey'] = '1'
    hapd = hostapd.add_ap(apdev[0], params)

    try:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "1")
        dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                       key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                       pairwise="CCMP")
        hapd.wait_sta();
        sta = hapd.get_sta(dev[0].own_addr())
        if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")

    finally:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "0")

def test_eppke_ap_gtk_rekey_with_base_akm_sae_ext_key_one_link(dev, apdev):
    """EPPKE AP and GTK rekey with MLO AP with 1 link"""
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface), \
        HWSimRadio(use_mlo=True) as (wpas_radio, wpas_iface):

        wpas = WpaSupplicant(global_iface='/tmp/wpas-wlan5')
        wpas.interface_add(wpas_iface)

        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt="SAE-EXT-KEY", mfp="2", pwe='1',
                                        beacon_prot=1)
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        params['wpa_group_rekey'] = '1'
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        wpas.set("sae_groups", "")
        wpas.set("sae_pwe", "1")
        wpas.connect(ssid, sae_password=passphrase, scan_freq="2412",
                     key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                     pairwise="CCMP GCMP-256")
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=1, active_links=1)

def test_eppke_ap_gtk_rekey_with_base_akm_sae_ext_key_two_link(dev, apdev):
    """EPPKE AP and GTK rekey with MLO AP with 2 links"""
    with HWSimRadio(use_mlo=True) as (hapd_radio, hapd_iface), \
        HWSimRadio(use_mlo=True) as (wpas_radio, wpas_iface):

        wpas = WpaSupplicant(global_iface='/tmp/wpas-wlan5')
        wpas.interface_add(wpas_iface)

        passphrase = '1234567890'
        ssid = "test-eppke-authentication"
        params = eht_mld_ap_wpa2_params(ssid, passphrase,
                                        key_mgmt="SAE-EXT-KEY", mfp="2", pwe='1',
                                        beacon_prot=1)
        params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'EPPKE'
        params['assoc_frame_encryption'] = '1'
        params['pmksa_caching_privacy'] = '1'
        params['eap_using_authentication_frames'] = '1'
        params['rsn_pairwise'] = "CCMP GCMP-256"
        params['wpa_group_rekey'] = '1'
        hapd0 = eht_mld_enable_ap(hapd_iface, 0, params)

        params['channel'] = '6'
        hapd1 = eht_mld_enable_ap(hapd_iface, 1, params)

        wpas.set("sae_groups", "")
        wpas.set("sae_pwe", "1")
        wpas.connect(ssid, sae_password=passphrase, scan_freq="2412 2437",
                     key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                     pairwise="CCMP GCMP-256")
        eht_verify_status(wpas, hapd0, 2412, 20, is_ht=True, mld=True,
                          valid_links=3, active_links=3)

def test_eppke_ap_ptk_rekey_with_base_akm_sae_ext_legacy_client(dev, apdev):
    """EPPKE AP and PTK rekey"""
    ssid = "test-eppke-authentication"
    passphrase = '1234567890'
    params = hostapd.wpa3_params(ssid=ssid,
				 password = passphrase)
    params['wpa_key_mgmt'] = params['wpa_key_mgmt'] + ' ' + 'SAE-EXT-KEY EPPKE'
    params['assoc_frame_encryption'] = '1'
    params['pmksa_caching_privacy'] = '1'
    params['eap_using_authentication_frames'] = '1'
    params['sae_pwe'] = '2'
    params['wpa_ptk_rekey'] = '2'
    hapd = hostapd.add_ap(apdev[0], params)

    try:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "1")
        dev[0].connect(ssid, sae_password=passphrase, scan_freq="2412",
                       key_mgmt="SAE-EXT-KEY", ieee80211w="2", beacon_prot="1",
                       pairwise="CCMP")
        hapd.wait_sta();
        sta = hapd.get_sta(dev[0].own_addr())
        if sta["AKMSuiteSelector"] != '00-0f-ac-24' or sta["auth_alg"] != '9':
            raise Exception("Incorrect Auth Algo/AKMSuiteSelector value")

    finally:
        dev[0].set("sae_groups", "")
        dev[0].set("sae_pwe", "0")
