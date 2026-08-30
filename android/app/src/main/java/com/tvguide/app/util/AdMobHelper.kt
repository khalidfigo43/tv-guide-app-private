package com.tvguide.app.util

import android.app.Activity
import android.content.Context
import android.util.Log
import com.google.android.gms.ads.AdError
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.FullScreenContentCallback
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.interstitial.InterstitialAd
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback

object AdMobHelper {
    private const val TAG = "AdMobHelper"

    // Master Switch to toggle Ads (Set to true when AdMob account is ready)
    const val ENABLE_ADS = false

    // Official Google Test Ad Unit IDs (replace with your production IDs in release)
    const val BANNER_AD_UNIT_ID = "ca-app-pub-3940256099942544/6300978111"
    const val INTERSTITIAL_AD_UNIT_ID = "ca-app-pub-3940256099942544/1033173712"

    private var interstitialAd: InterstitialAd? = null
    private var isAdLoading = false
    private var clickCount = 0
    private const val CLICKS_BETWEEN_ADS = 4

    fun initialize(context: Context) {
        if (!ENABLE_ADS) return
        try {
            MobileAds.initialize(context) { initializationStatus ->
                Log.d(TAG, "AdMob Initialized: $initializationStatus")
                loadInterstitialAd(context)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun loadInterstitialAd(context: Context) {
        if (!ENABLE_ADS) return
        if (interstitialAd != null || isAdLoading) return
        isAdLoading = true

        val adRequest = AdRequest.Builder().build()
        InterstitialAd.load(
            context,
            INTERSTITIAL_AD_UNIT_ID,
            adRequest,
            object : InterstitialAdLoadCallback() {
                override fun onAdLoaded(ad: InterstitialAd) {
                    interstitialAd = ad
                    isAdLoading = false
                    Log.d(TAG, "Interstitial Ad Loaded successfully")
                }

                override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                    interstitialAd = null
                    isAdLoading = false
                    Log.e(TAG, "Interstitial Ad Failed to load: ${loadAdError.message}")
                }
            }
        )
    }

    fun showInterstitialAdIfReady(activity: Activity?, onDismissed: () -> Unit = {}) {
        if (!ENABLE_ADS) {
            onDismissed()
            return
        }

        clickCount++
        if (clickCount % CLICKS_BETWEEN_ADS != 0) {
            onDismissed()
            return
        }

        if (activity != null && interstitialAd != null) {
            interstitialAd?.fullScreenContentCallback = object : FullScreenContentCallback() {
                override fun onAdDismissedFullScreenContent() {
                    interstitialAd = null
                    loadInterstitialAd(activity)
                    onDismissed()
                }

                override fun onAdFailedToShowFullScreenContent(adError: AdError) {
                    interstitialAd = null
                    loadInterstitialAd(activity)
                    onDismissed()
                }
            }
            interstitialAd?.show(activity)
        } else {
            activity?.let { loadInterstitialAd(it) }
            onDismissed()
        }
    }
}
