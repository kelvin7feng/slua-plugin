1.android构建步骤(Mac OS)：
	1.把NDK路径添加到环境变量里: vim ~/.bash_profile
	2.添加NDKPATH(把NDKPATH改成本机路径):
		export NDKPATH=/Users/Kelvin/application/android-ndk-r16
		export PATH=/Users/Kelvin/application/redis/src:${NDKPATH}:${PATH}
	3.source ~/.bash_profile
	4.执行make_android.sh