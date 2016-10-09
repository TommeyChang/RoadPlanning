#coding=utf8

import os, os.path, sys, logging
from scipy import misc
import numpy, turtle, copy

########################################################################
class MapPreprocess:
    """load the raw map, then transfer it to a binary map, at last create a grid map"""
    
    Table =(0,0,0,0,0,0,0,1,    0,0,1,1,0,0,1,1,
            0,0,0,0,0,0,0,0,    0,0,1,1,1,0,1,1,
            0,0,0,0,0,0,0,0,    1,0,0,0,1,0,1,1,
            0,0,0,0,0,0,0,0,    1,0,1,1,1,0,1,1,
            0,0,0,0,0,0,0,0,    0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,    0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,    1,0,0,0,1,0,1,1,
            1,0,0,0,0,0,0,0,    1,0,1,1,1,0,1,1,
            0,0,1,1,0,0,1,1,    0,0,0,1,0,0,1,1,
            0,0,0,0,0,0,0,0,    0,0,0,1,0,0,1,1,
            1,1,0,1,0,0,0,1,    0,0,0,0,0,0,0,0,
            1,1,0,1,0,0,0,1,    1,1,0,0,1,0,0,0,
            0,1,1,1,0,0,1,1,    0,0,0,1,0,0,1,1,
            0,0,0,0,0,0,0,0,    0,0,0,0,0,1,1,1,
            1,1,1,1,0,0,1,1,    1,1,0,0,1,1,0,0,
            1,1,1,1,0,0,1,1,    1,1,0,0,1,1,0,0)
    
    aroundPos = ((0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1))
    aroundCon = ((1,1), (1,-1), (-1,1), (-1,-1), (0,-1), (1,0), (0,1), (-1,0))

    #将黑白图像进行二值化，然后进行存储
    def __init__(self, bMapName = './map/hefei/hefei_pro.png'):
        """
        Constructor:
        load the map
        """ 
        print '开始加载原始图像...'
        mapImageData = misc.imread(bMapName)
        misc.imshow(mapImageData)
        imageData = numpy.array(mapImageData[:,:,0])
        mean = imageData.mean()
        upper = imageData > mean
        lowwer = imageData < mean
        imageData[upper] = 255
        imageData[lowwer] = 0        
        self.imageData = imageData
        self.imageDataShape = imageData.shape
        print '原始图像加载完毕。'
        self.roadImageExtract()
        
    
    # 从二值化图像中抽取道路主干
    def roadImageExtract(self):
        print '开始抽取道路主干...'
        rawImageData = numpy.array(self.imageData)
        shape = self.imageDataShape
        # 第一步， 使用模板法获取道路的主干 
        
        mainImageData = self.roadMainExtact(shape, rawImageData) 
        
        # 第二步， 消除道路中存在的毛刺
        roadData = self.eliminatePin(shape, mainImageData, 5)        
        
        self.roadImageData = roadData
        print '道路主干抽取完成。'
    
    def roadMainExtact(self, shape, imageData):       
        for i in range(11): 
            # 垂直扫描
            for vertical in range(shape[0]):
                start = 1
                for horizen in range(shape[1]):
                    # 如果当前点为黑色，查找删除列表，如果能被删除，刚将其从图像中删除
                    if imageData[vertical][horizen] < 125 and start:
                        if imageData[vertical][horizen + 1] > 125 or imageData[vertical][horizen - 1] > 125:                            
                            situation = 0                        
                            for each in self.aroundPos:
                                situation <<= 1
                                if imageData[vertical + each[0]][horizen + each[1]] < 125:
                                    situation |= 1
                            if self.Table[situation] == 1:
                                imageData[vertical][horizen] = 255 
                                start = 0
                    else:
                        start = 1
            # 水平扫描               
            for horizen in range(shape[1]):
                start = 1
                for vertical in range(shape[0]):
                    # 如果有一个点为黑色，查找删除列表，如果能被删除，刚将其从图像中删除
                    if imageData[vertical][horizen] < 125 and start :
                        if imageData[vertical + 1][horizen] > 125 or imageData[vertical - 1][horizen] > 125:                            
                            situation = 0                        
                            for each in self.aroundPos:
                                situation <<= 1
                                if imageData[vertical + each[0]][horizen + each[1]] < 125:
                                    situation |= 1
                            if self.Table[situation] == 1:
                                imageData[vertical][horizen] = 255  
                                start = 0
                    else:
                        start = 1   
        return imageData
                    
                    
   # 消除行刺
    def eliminatePin(self, shape, imageData, pinLen):
        for vertical in range(shape[0]):            
            for horizen in range(shape[1]): 
                # 对于一个黑色像素点， 首先计算其分支数
                if imageData[vertical][horizen] < 255:
                    branchFactor, branchList = self.branchFactorCom(imageData, (vertical, horizen))
                    if branchFactor == 1:
                        # 如果分支数为1, 那么该点是路径的端点， 建立一个路径列表， 表头为当前点
                        pathList = [(vertical, horizen)]                        
                        for i in range(pinLen):
                            # 查找周围, 找出路径头部点的分支因子， 以及新的分支点
                            connectNumber = 0
                            for each in self.aroundCon:
                                surrond = (pathList[0][0] + each[0], pathList[0][1] + each[1])
                                if imageData[surrond[0]][surrond[1]]  < 100 :
                                    connectNumber += 1
                                    if surrond not in pathList:
                                        branchList = surrond
                            if connectNumber <= 2:
                                # 说明尚未遇到， 将新的分支插入路径列表头部， 作为下一次路径扩展点
                                pathList.insert(0, branchList)                                
                            else:
                                # 先将交叉点以外的路径去掉
                                begin = 1                                
                                subBranchFactor, subBranchList = self.branchFactorCom(imageData, pathList[0])
                                if subBranchFactor == 2:
                                    begin = 0                                    
                                for path in pathList[begin:]:
                                    imageData[path[0]][path[1]] = 255
                                break
        return imageData
        
    
   
    
    # 设置公交路线
    def busSetter(self, overlapFactor = 0): # 参数为路径重复率
        busStationX, busStationY = 0,0 
        crossAmount = 0
        
        # 找出图中节点的一个算术几何中心
        for key in self.crossDic:
            crossAmount += 1
            busStationX += key[0]
            busStationY += key[1]
        busStationX = busStationX / crossAmount
        busStationY = busStationY / crossAmount
        gap = 1000000
        
        # 将离该几何中心最近一个交叉路口作为车站
        for key in self.crossDic:
            distance = abs(key[0] - busStationX) + abs(key[1] - busStationY)
            if distance < gap:
                station = key
                gap = distance        
                
        # 从每一个端点出发， 找一条最近的道路到达目标
        busLineList = []
        for terminalKey, terminalItem in self.terminalDic.items():
            frontierList = [terminalItem['NextTo']]
            exploredList = []
            pathCost = terminalItem['PathLength']
            pathTreeDic = { frontierList[0] : {'FatherNode' : terminalKey, 'PathCost' : terminalItem['PathLength']} }
            
            while True:
                frontierPoint = frontierList.pop(0)
                if frontierPoint == station:
                    busLine = [station]
                    pathLength = pathTreeDic[station]['PathCost']
                    while True:
                        preNode = pathTreeDic[busLine[0]]['FatherNode']
                        busLine.insert(0, preNode)
                        if preNode == terminalKey:
                            break
                    #按照路径距离降序进行排列
                    indexBusLine = 0
                    unAppendFlag = 1
                    for eachBusLine in busLineList:
                        if pathLength > eachBusLine[1]:
                            busLineList.insert(indexBusLine, (busLine, pathLength))
                            unAppendFlag = 0
                            break
                        indexBusLine += 1                        
                    if unAppendFlag:
                        busLineList.append((busLine, pathLength))
                    break
                    
                else:
                    for subPath in self.crossDic[frontierPoint]:
                        nextPoint = subPath['NextTo']
                        if subPath['NeighborType'] == 'C' and nextPoint not in exploredList:                            
                            hPathLength = abs(nextPoint[0] - station[0]) + abs(nextPoint[1] - station[1])
                            totalPathLength = hPathLength + subPath['PathLength'] + pathTreeDic[frontierPoint]['PathCost']
                            if nextPoint in frontierList:
                                if pathTreeDic[nextPoint]['PathCost'] < totalPathLength:
                                    continue
                                else:
                                    frontierList.remove(nextPoint)                            
                            # 将当前点插入比其路径代价小的点之前
                            unInsertFlag = 1
                            for eachFrontierIndex, eachFrontier in enumerate(frontierList):
                                if totalPathLength < pathTreeDic[eachFrontier]['PathCost']:
                                    frontierList.insert(eachFrontierIndex, nextPoint)
                                    unInsertFlag = 0
                                    break
                            if unInsertFlag :
                                frontierList.append(nextPoint) 
                            pathTreeDic[nextPoint] = { 'FatherNode' : frontierPoint, 'PathCost' : totalPathLength }
                    exploredList.append(frontierPoint)
        
        
        
        #构建一棵路径树， 根节点是中心车站， 叶子节点为各端点
        exploredNodeSet = set()
        # 目标点总是会重合        
        
        lineKeepList = []
        count = 0
        for eachBusLine in busLineList:
            count += 1
            overlapNumber = 0
            pathLength = 0
            for eachStep in eachBusLine[0]:
                pathLength += 1
                if eachStep in exploredNodeSet:
                    overlapNumber += 1
            if overlapNumber != 0:
                overlapNumber -= 1
            
            if 100 * overlapNumber / pathLength < overlapFactor :
                lineKeepList.append(eachBusLine[0])
                for eachItem in eachBusLine[0]:
                    exploredNodeSet.add(eachItem)
                
        self.drawResult(self.crossDic,self.terminalDic,lineKeepList,station)      
            
    
    # 计算分支因子， 并找出后续扩展点
    def branchFactorCom(self, imageData, pos, exploredList = []):
        # 找出一个白点
        for i in range(8):
            if imageData[pos[0] + self.aroundPos[i][0]][pos[1] + self.aroundPos[i][1]] > 200:
                localAround = self.aroundPos[i:] + self.aroundPos[ : i + 1] 
                break
            
        branchList = []
        changeTimes = 0
        conNumber = 0
        conList = []        
        # 计算当前点的分支因子， 并找出后续的扩展点
        previousPos = ((pos[0] + localAround[0][0]), (pos[1] + localAround[0][1]))
        previousState = 255          
        for each in localAround[1:]:
            currentPos = ((pos[0] + each[0]), (pos[1] + each[1]))
            currentState = imageData[currentPos[0]][currentPos[1]]
            
            # 如果出现黑色像素点， 并且没有被扩展, 则将其加入列表中， 并增加连接数
            if currentState < 200 :
                if currentPos not in exploredList:
                    conNumber += 1
                    conList.append(currentPos)
            else:
                if conNumber > 1 :
                    # 找出每个连接点的子分支因子， 然后按照分支因子降序排列
                    subBrachFactorList = []
                    for unit in conList:
                        # 先找到一个白点
                        for i in range(8):
                            if imageData[unit[0] + self.aroundPos[i][0]][unit[1] + self.aroundPos[i][1]] > 200:
                                subLocalAround = self.aroundPos[ i : ] + self.aroundPos[ : i + 1]
                                break                        
                        preState = 255
                        subChangTimes = 0
                        for around in subLocalAround[1:]:
                            curState = imageData[unit[0] + around[0]][unit[1] + around[1]]
                            if curState != preState:
                                subChangTimes += 1
                                preState = curState
                        subBrachFactorList.append(subChangTimes)
                    while subBrachFactorList:
                        maxIndex = subBrachFactorList.index(max(subBrachFactorList))
                        branchList.append(conList.pop(maxIndex))                        
                        subBrachFactorList.pop(maxIndex)                        
                elif conNumber == 1:
                    branchList.append(conList[0])
                conNumber = 0 
                conList = []
                    
            if currentState != previousState:                
                changeTimes += 1
                previousState = currentState
            
        # 比较变化次数和连接数
                    
        branchFactor = changeTimes / 2
        return branchFactor, branchList  
    
    # 提取道路信息， 建立路网import turtle
    def roadGridExtract(self):
        print '开始提取路网信息...'
        roadImageData = self.roadImageData
        shape = self.imageDataShape
        terminalDic = {}
        crossDic = {}
        
        crossList = []
        # 遍历全图， 找到所有的端点和交叉点
        for vertical in range(shape[0]):
            for horizen in range(shape[1]):
                if roadImageData[vertical][horizen] < 200:
                    branchFactor, branchList = self.branchFactorCom(roadImageData, (vertical, horizen))
                    if branchFactor == 1:
                        terminalDic[(vertical, horizen)] = {}
                    elif branchFactor > 2:
                        crossList.append((vertical, horizen))      
       
        # 将交叉点分组， 并建立点与组之间的映射关系
        
        gapFactor = 5
        groupMapDic = {}
        groupList = []
        
        while crossList: 
            crossGroup = [crossList[0]]      
            for eachCross in crossList[1:]:
                xGap = abs(eachCross[0] - crossList[0][0])
                yGap = abs(eachCross[1] - crossList[0][1])
                totalGap =  xGap + yGap 
                if totalGap  <= gapFactor * 1.4:                    
                    crossGroup.append(eachCross)
            # 从交叉路口列表中删掉已经编组的点, 将同一组中的元素设置相同的组别编码
            for eachElement in crossGroup:
                crossList.pop(crossList.index(eachElement))     
                groupMapDic[eachElement] = crossGroup[0]
            # 以组名建立一个交叉路口列表
            crossDic[crossGroup[0]] = []
            # 将本组元素加入到组列表中
            groupList.append(crossGroup)
        
        
        for eachGroup in groupList:           
            for eachCrossPoint in eachGroup:
                branchFactor, branchList = self.branchFactorCom(roadImageData, eachCrossPoint) 
                exploredTerminal = []
                # 依次扩展路口周边的每一个分支点 
                
                for eachBranch in branchList:
                    exploredList = []                
                    frontierList = [eachBranch]
                    pathLen = 1
                    while frontierList:
                        currentPos = frontierList[0]
                        curBranchFactor, curBranchList = self.branchFactorCom(roadImageData, currentPos, frontierList + exploredList + [eachCrossPoint] + branchList)
                        if curBranchFactor == 1: 
                            if currentPos not in exploredTerminal:                                
                                terminalDic[currentPos]['NextTo'] = groupMapDic[eachCrossPoint]
                                terminalDic[currentPos]['PathLength'] = pathLen
                                crossDic[eachGroup[0]].append({'NextTo': currentPos, 'NeighborType' : 'T' , 'PathLength' : pathLen})
                                exploredTerminal.append(currentPos)
                            break
                        elif curBranchFactor == 2:
                            pathLen += 1
                            exploredList.append(frontierList.pop(0))
                            frontierList = curBranchList + frontierList
                        else:
                            if (groupMapDic[currentPos] != eachGroup[0]) and (currentPos not in exploredTerminal) :
                                crossDic[eachGroup[0]].append({'NextTo': groupMapDic[currentPos], 'NeighborType' : 'C', 'PathLength' : pathLen})
                                exploredTerminal.append(currentPos)
                            break
        self.crossDic = crossDic
        self.groupMapDic = groupMapDic
        self.terminalDic = terminalDic
        
        print '路网信息提取完毕。'
        
        
    def p2pPathFinder(self, srcPoint, desPoint):
        print '开始查找最短路径...'
        # conCross, conCrossNumber, approachPoint
        # 首先计算出每个点的连接数和连接类型
        srcPointCon = self.approachPath(srcPoint)
        desPointCon = self.approachPath(desPoint)
        crossDic = copy.deepcopy(self.crossDic)
        
        # 首先对目标点进行处理。 对于不同的连接类型， 目标测试方法不同， 如果接近点是端点， 那么只要接近点叉路口的邻居中， 路径就已经找到； 如果接近点是交叉路口， 那么接近点必须被扩展时， 才表示路径已经找到； 如果接近点是在道路中间， 如果位于端点与交叉路口连接的道路中， 和端点处理方法相同； 如果位于两个叉路口之间， 那么该点就是一个新的叉路口， 和叉路口的处理方法相同  
        if desPointCon[1] == 3:
            # 计算出分支路径数量， 如果为1, 说明位于端点与交叉路口之间， 否则为交叉路口之间
            conType = len(desPointCon[0])
            for eachCon in desPointCon[0]:
                if conType > 1 :
                    crossDic[eachCon['NextTo']].append({'NextTo': desPointCon[2], 'NeighborType' : 'C', 'PathLength' : eachCon['PathLength'] })
                else:
                    crossDic[eachCon['NextTo']].append({'NextTo': desPointCon[2], 'NeighborType' : 'T', 'PathLength' : eachCon['PathLength'] })
        else:
            conType = desPointCon[1]
        
        desApproachPoint = desPointCon[2]
        
        # 将接触点非为交叉路口的点加入交叉路口字典
        
        if srcPointCon[1] == 1:
            crossDic[srcPointCon[2]] = [{'NextTo': self.terminalDic[srcPointCon[2]]['NextTo'], 'NeighborType' : 'C', 'PathLength' : self.terminalDic[srcPointCon[2]]['PathLength'] }]           
        elif srcPointCon[1] == 3:
            crossDic[srcPointCon[2]] = srcPointCon[0]  
            
        pathTreeDic = {}
        frontierList = [srcPointCon[2]]        
        pathCost = srcPointCon[3] + desPointCon[3]
        pathTreeDic[frontierList[0]] = {'FatherNode' : srcPoint, 'PathCost' : pathCost} 
        
        reachFlag = 0
        exploredList = []
        
        while True:
            # 从 frontierList 中弹出队首元素作为扩展点           
            frontierPoint = frontierList.pop(0)            
            if conType == 2 :
                # 对于接触点是交叉路口的， 如果扩展点是目标点的接触点， 那么表示已经找到路径, 用回溯的方法构建路径
                if frontierPoint == desApproachPoint:
                    reachFlag = 1
                    pathLength = pathTreeDic[frontierPoint]['PathCost']
                    pathList = [desApproachPoint, desPoint]
                    while True:
                        fatherPoint = pathTreeDic[pathList[0]]['FatherNode']
                        pathList.insert(0, fatherPoint)
                        if fatherPoint == srcPoint: 
                            break
                else:
                    # 对于每一条子路径
                    for eachPath in crossDic[frontierPoint]:
                        # 如果连接的是交叉路口, 且不是父节点, 且未被扩展
                        nextPoint = eachPath['NextTo']
                        if (eachPath['NeighborType'] == 'C') and (nextPoint != frontierPoint) and (nextPoint not in exploredList):
                            # 使用曼哈顿距离作为启发函数
                            hPathLength = abs(nextPoint[0] - desPoint[0]) + abs(nextPoint[1] - desPoint[1])
                            totalPathLength = hPathLength + eachPath['PathLength'] + pathTreeDic[frontierPoint]['PathCost']
                            # 如果下一个交叉点已经在队列中， 并且路径开销小于当前开销， 那么跳过， 否则将其从队列中删除
                            if nextPoint in frontierList:
                                if pathTreeDic[nextPoint]['PathCost'] < totalPathLength:
                                    continue
                                else:
                                    frontierList.remove(nextPoint)                            
                            # 将当前点插入比其路径代价小的点之前
                            unInsertFlag = 1
                            for eachFrontierIndex, eachFrontier in enumerate(frontierList):
                                if totalPathLength < pathTreeDic[eachFrontier]['PathCost']:
                                    frontierList.insert(eachFrontierIndex, nextPoint)
                                    unInsertFlag = 0
                                    break
                            if unInsertFlag :
                                frontierList.append(nextPoint)
                            # 树字典中建立该节点的信息
                            pathTreeDic[nextPoint] = { 'FatherNode' : frontierPoint, 'PathCost' : totalPathLength }
            else:
                for eachPath in crossDic[frontierPoint]:
                    nextPoint = eachPath['NextTo']
                    if eachPath['NeighborType'] == 'T':
                        
                        # 对于接触点是端点的， 由于通往端点的交叉路口只有一个， 如果该端点在当前点的下一步节点中， 表明路径已经找到
                        if nextPoint == desApproachPoint:
                            reachFlag = 1
                            pathLength = pathTreeDic[frontierPoint]['PathCost'] + eachPath['PathLength']
                            pathList = [frontierPoint, desApproachPoint, desPoint]
                            while True:
                                fatherPoint = pathTreeDic[pathList[0]]['FatherNode']
                                pathList.insert(0, fatherPoint)
                                if fatherPoint == srcPoint: 
                                    break 
                    else:
                        if nextPoint not in exploredList :
                            
                            # 使用曼哈顿距离作为启发函数
                            hPathLength = abs(nextPoint[0] - desPoint[0]) + abs(nextPoint[1] - desPoint[1])
                            totalPathLength = hPathLength + eachPath['PathLength'] + pathTreeDic[frontierPoint]['PathCost']
                            
                            # 如果下一个交叉点已经在队列中， 并且路径开销小于当前开销， 那么跳过， 否则将其从队列中删除
                            if nextPoint in frontierList:
                                if pathTreeDic[nextPoint]['PathCost'] < totalPathLength:
                                    continue
                                else:
                                    frontierList.remove(nextPoint) 
                                    
                            # 将当前点插入比其路径代价小的点之前
                            unInsertFlag = 1
                            for eachFrontierIndex, eachFrontier in enumerate(frontierList):
                                if totalPathLength < pathTreeDic[eachFrontier]['PathCost']:
                                    frontierList.insert(eachFrontierIndex, nextPoint)
                                    unInsertFlag = 0
                                    break
                            if unInsertFlag:
                                frontierList.append(nextPoint)
                            # 在树字典中建立该节点的信息
                            pathTreeDic[nextPoint] = { 'FatherNode' : frontierPoint, 'PathCost' : totalPathLength }
                                
            if reachFlag:
                break
            exploredList.append(frontierPoint)
        print '最短路径查找完成。'        
        
        self.drawResult(crossDic, self.terminalDic, pathList)
            
                        
    def drawResult(self, crossDic, terminalDic, pathList = [], pathListDim = 1):
        
        reload(turtle)
        
        print '开始绘制路网信息...' 
        
        turtle.hideturtle()  
        turtle.speed(1000)           
        turtle.begin_fill()
        turtle.color('black')
        
        width = self.imageDataShape[1] / 2 + 1
        length = self.imageDataShape[0] / 2 + 1
    
        for point in terminalDic:            
            turtle.penup()
            width = 500
            length = 310
            turtle.goto(point[1] * 1.5 - width * 1.5, length * 1.5 - point[0] * 1.5 )
            turtle.pendown()
            turtle.begin_fill()
            turtle.color('black')            
            turtle.circle(1)
            turtle.end_fill()
    
        for point in crossDic:
            turtle.penup()
            turtle.goto(point[1] * 1.5 - width * 1.5, length * 1.5 - point[0] *1.5)
            turtle.pendown()
            turtle.begin_fill()
            turtle.color('black')            
            turtle.circle(2)
            turtle.end_fill()
    
            for terminal in crossDic[point]:
                turtle.penup()
                turtle.goto(point[1] * 1.5 - width * 1.5, length * 1.5 - point[0] *1.5)
                turtle.pendown()                 
                turtle.goto(terminal['NextTo'][1] * 1.5 - width * 1.5, length * 1.5 - terminal['NextTo'][0] * 1.5)  
        
        print '路网信息绘制完成。'           
        
        if len(pathList) == 0:            
            return
        
        print '开始绘制路径...'
            
        if pathListDim == 1:        
            turtle.penup()
            turtle.goto(pathList[0][1] * 1.5 - width * 1.5, length * 1.5 - pathList[0][0] *1.5)
            turtle.pendown()
            turtle.color('red') 
            turtle.pensize(2)
            turtle.begin_fill()            
            turtle.circle(4)
            turtle.end_fill()        
            for eachPoint in pathList[1:]: 
                turtle.goto(eachPoint[1] * 1.5 - width * 1.5, length * 1.5 - eachPoint[0] *1.5)
                turtle.begin_fill()            
                turtle.circle(4)
                turtle.end_fill()   
        else:
            for eachPath in pathList:
                turtle.penup()
                turtle.goto(eachPath[0][1] * 1.5 - width * 1.5, length * 1.5 - eachPath[0][0] *1.5)
                turtle.pendown()
                turtle.color('red') 
                turtle.pensize(2)
                turtle.begin_fill()            
                turtle.circle(3)
                turtle.end_fill()        
                for eachPoint in eachPath[1:]: 
                    turtle.goto(eachPoint[1] * 1.5 - width * 1.5, length * 1.5 - eachPoint[0] *1.5)
                    turtle.begin_fill()            
                    turtle.circle(4)
                    turtle.end_fill()  
                    
            turtle.penup()
            turtle.goto(pathListDim[1] * 1.5 - width * 1.5, length * 1.5 - pathListDim[0] *1.5)
            turtle.pendown()
            turtle.color('blue') 
            turtle.pensize(2)
            turtle.begin_fill()            
            turtle.circle(8, steps = 6)
            turtle.end_fill()              
        
            
            
        
        print '路径绘制完成。'
                          
    
        turtle.done()
        
                    
        
    
    def approachPath(self, point):
        distance = 1
        approachPoint = (-1, -1)
        
        while approachPoint[0] == -1:
            # 遍历与目标点距离等于 distance 的所有点， 如果找到一个路径黑点， 就停止
            upper = - distance
            lower = distance + 1
            
            for verticl in range(upper, lower, 1):                
                horezen = distance - abs(verticl)
                if self.roadImageData[point[0] + verticl][point[1] + horezen] < 200:
                    approachPoint =  ( point[0] + verticl, point[1] + horezen)                    
                    break
                horezen = - horezen
                if self.roadImageData[point[0] + verticl][point[1] + horezen] < 200:
                    approachPoint =  ( point[0] + verticl, point[1] + horezen)                    
                    break
                
            distance += 1
        
        subBranchFactor, subBranchPath = self.branchFactorCom(self.roadImageData, approachPoint)
        if subBranchFactor == 1:
            return [], 1, approachPoint, distance
        
        elif subBranchFactor == 3:
            return [], 2, approachPoint, distance
        
        else:
            conCross = []            
            exploredList = [approachPoint]            
            for eachPath in subBranchPath:
                pathLen = 1 
                frontierList = [eachPath]
                while frontierList:
                    sBranchFactor , sBranchPath = self.branchFactorCom(self.roadImageData, frontierList[0], exploredList)
                    if sBranchFactor == 1:
                        break
                    elif sBranchFactor == 2:
                        exploredList.append(frontierList.pop(0))
                        pathLen += 1
                        frontierList = sBranchPath
                    elif sBranchFactor > 2:
                        conCross.append({'NextTo': self.groupMapDic[frontierList[0]], 'NeighborType' : 'C', 'PathLength' : pathLen})
                        
                        break
            
            return conCross, 3, approachPoint, distance
            



if __name__ == '__main__':        
    test = MapPreprocess('./map/hefei/hefei_pro.png')    
    test.roadGridExtract()
    test.drawResult(test.crossDic,test.terminalDic)
    test.p2pPathFinder((100, 120), (200, 900))
    test.busSetter(20) 