# AutoMinesweeper
自动扫雷

## TODO
* [ ] 准备跨平台，先要确定平台:
*  * visual studio - C# xamarin
*  * visual studio - c++ lib + GDI + NDK + Native-Android
*  * Qt - c++ lib + QML
*  * ...

c++ lib 开发:
-  [ ] 扫雷生成
-  [ ] 扫雷AI
-  [ ] 基于穷举雷所有的分布局面，动态计算雷的分布概率
-  [ ] 无猜相关
- -   [ ] 动态调整雷的分布使得整个扫雷过程无猜
- -   [ ] 动态调整雷的分布使得死猜情况下雷只会在概率较大处（概率相同时直接调整为无猜）
* [ ] console下的简单运行和测试
* [ ] win ui
* [ ] android ui
