#!/usr/bin/env python
# coding: utf-8
# alvin@2013-05-18 14:06:52
# vim: set noexpandtab tabstop=4 shiftwidth=4 softtabstop=4:

import sys
import time
import os
import errno
import wx
import yaml
import shutil
from wx.lib.wordwrap import wordwrap
from mako.template import Template
import logging

import subprocess

ROOT_DIR = os.getcwd()

CONFIG_FILE = '%s/config/config.yaml' % ROOT_DIR

ID_REFRESH =  wx.NewId()
ID_EXIT  =  wx.NewId()
ID_HELP =  wx.NewId()
ID_ABOUT =  wx.NewId()

def initLog(logFile, level):
	_logger = logging.getLogger('root')

	_formatter = logging.Formatter('%(asctime)s %(levelname)s %(pathname)s %(funcName)s %(lineno)d %(process)d %(thread)d %(threadName)s: %(message)s')
	_handler = logging.FileHandler(logFile)
	_handler.setFormatter(_formatter)
	_handler.setLevel(level)

	_logger.addHandler(_handler)
	return _logger

logFile = '%s/logs/trace.log' % ROOT_DIR
LOGGER = initLog(logFile, logging.DEBUG)

class DragListStriped(wx.ListCtrl):
	def __init__(self, *arg, **kw):
		wx.ListCtrl.__init__(self, *arg, **kw)
 
		self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._onDrag)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._onSelect)
		self.Bind(wx.EVT_LEFT_UP,self._onMouseUp)
		self.Bind(wx.EVT_LEFT_DOWN, self._onMouseDown)
		self.Bind(wx.EVT_LEAVE_WINDOW, self._onLeaveWindow)
		self.Bind(wx.EVT_ENTER_WINDOW, self._onEnterWindow)
		self.Bind(wx.EVT_LIST_INSERT_ITEM, self._onInsert)
		self.Bind(wx.EVT_LIST_DELETE_ITEM, self._onDelete)
		self.Bind(wx.EVT_LIST_KEY_DOWN, self._listEvtKeyDown)
 
		#---------------
		# Variables
		#---------------
		self.IsInControl=True
		self.startIndex=-1
		self.dropIndex=-1
		self.IsDrag=False
		self.dragIndex=-1
 
	def _onLeaveWindow(self, event):
		self.IsInControl=False
		self.IsDrag=False
		event.Skip()
 
	def _onEnterWindow(self, event):
		self.IsInControl=True
		event.Skip()
 
	def _onDrag(self, event):
		self.IsDrag=True
		self.dragIndex=event.m_itemIndex
		event.Skip()
		pass
 
	def _onSelect(self, event):
		self.startIndex=event.m_itemIndex
		event.Skip()

	def _listEvtKeyDown(self, event): # wxGlade: MyFrame1.<event_handler>
		keycode = event.GetKeyCode()
		#print "Event handler `ListEvtKeyDown' " + str(keycode)
		if keycode == wx.WXK_DELETE:
			self.DeleteItem(self.GetFocusedItem())

		elif keycode == wx.WXK_RIGHT:
			self._moveDown(event)
		elif keycode == wx.WXK_LEFT:
			self._moveUp(event)

	def _moveUp(self, event):
		#__import__('pdb').set_trace()
		if 0 == self.startIndex: # 第一条
			pass
		else:
			dropList = []
			prevItem = self.GetItem(self.startIndex - 1)
			for x in range(self.GetColumnCount()):
				dropList.append(self.GetItem(self.startIndex - 1,x).GetText())
			prevItem.SetId(self.startIndex)
			self.DeleteItem(self.startIndex - 1)
			#self.SetItemBackgroundColour(prevItem,wx.Colour(255,255,0))
			#self.SetItemTextColour(self.startIndex, wx.Colour(255,255,0))
			self.InsertItem(prevItem)
			for x in range(self.GetColumnCount()):
				self.SetStringItem(self.startIndex, x, dropList[x])
			self.Select(self.startIndex - 1, on=1)
			self.startIndex -= 1
		self._onStripe()
		self.IsDrag=False
		event.Skip()
 
	def _moveDown(self, event):
		#__import__('pdb').set_trace()
		if self.GetItemCount() == self.startIndex + 1: # 最后一条
			pass
		else:
			dropList = []
			nextItem = self.GetItem(self.startIndex + 1)
			for x in range(self.GetColumnCount()):
				dropList.append(self.GetItem(self.startIndex + 1,x).GetText())
			nextItem.SetId(self.startIndex)
			self.DeleteItem(self.startIndex + 1)
			self.InsertItem(nextItem)
			for x in range(self.GetColumnCount()):
				self.SetStringItem(self.startIndex, x, dropList[x])
			self.Select(self.startIndex + 1, on=1)
			self.startIndex += 1
		self._onStripe()
		self.IsDrag=False
		event.Skip()
 
	def _onMouseUp(self, event):
		# Purpose: to generate a dropIndex.
		# Process: check self.IsInControl, check self.IsDrag, HitTest, compare HitTest value
		# The mouse can end up in 5 different places:
		# Outside the Control
		# On itself
		# Above its starting point and on another item
		# Below its starting point and on another item
		# Below its starting point and not on another item
 
		if self.IsInControl==False:	  #1. Outside the control : Do Nothing
			self.IsDrag=False
		else:								  # In control but not a drag event : Do Nothing
			if self.IsDrag==False:
				pass
			else:							  # In control and is a drag event : Determine Location
				self.hitIndex=self.HitTest(event.GetPosition())
				self.dropIndex=self.hitIndex[0]
				# -- Drop index indicates where the drop location is; what index number
				#---------
				# Determine dropIndex and its validity
				#--------
				if self.dropIndex==self.startIndex or self.dropIndex==-1:	#2. On itself or below control : Do Nothing
					pass
				else:
					#----------
					# Now that dropIndex has been established do 3 things
					# 1. gather item data
					# 2. delete item in list
					# 3. insert item & it's data into the list at the new index
					#----------
					dropList=[]		# Drop List is the list of field values from the list control
					thisItem=self.GetItem(self.startIndex)
					for x in range(self.GetColumnCount()):
						dropList.append(self.GetItem(self.startIndex,x).GetText())
					thisItem.SetId(self.dropIndex)
					self.DeleteItem(self.startIndex)
					self.InsertItem(thisItem)
					for x in range(self.GetColumnCount()):
						self.SetStringItem(self.dropIndex,x,dropList[x])
			#------------
			# I don't know exactly why, but the mouse event MUST
			# call the stripe procedure if the control is to be successfully
			# striped. Every time it was only in the _onInsert, it failed on
			# dragging index 3 to the index 1 spot.
			#-------------
			# Furthermore, in the load button on the wxFrame that this lives in,
			# I had to call the _onStripe directly because it would occasionally fail
			# to stripe without it. You'll notice that this is present in the example stub.
			# Someone with more knowledge than I probably knows why...and how to fix it properly.
			#-------------
		self._onStripe()
		self.IsDrag=False
		event.Skip()
 
	def _onMouseDown(self, event):
		self.IsInControl=True
		event.Skip()
 
	def _onInsert(self, event):
		# Sequencing on a drop event is:
		# wx.EVT_LIST_ITEM_SELECTED
		# wx.EVT_LIST_BEGIN_DRAG
		# wx.EVT_LEFT_UP
		# wx.EVT_LIST_ITEM_SELECTED (at the new index)
		# wx.EVT_LIST_INSERT_ITEM
		#--------------------------------
		# this call to onStripe catches any addition to the list; drag or not
		self._onStripe()
		self.dragIndex=-1
		event.Skip()
 
	def _onDelete(self, event):
		self._onStripe()
		event.Skip()
 
	def _onStripe(self):
		if self.GetItemCount()>0:
			for x in range(self.GetItemCount()):
				if x % 2==0:
					self.SetItemBackgroundColour(x,wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DLIGHT))
				else:
					self.SetItemBackgroundColour(x,wx.WHITE)

class NCString(wx.Frame):
	def __init__(self, parent, title):
		super(NCString, self).__init__(parent, title=title, size=(600, 520))
		self._TEMPLATES = [] 
		self.templateChoices = []
		self.src = ROOT_DIR
		self.loadDefault = True
		self.loadConfig()
		self.files = []
		self.isFolder = False
		self.initUI()
		self.Centre()
		self.Show()

	def loadConfig(self):
		LOGGER.info(u'Loading Config from %s...' % CONFIG_FILE)
		with open(CONFIG_FILE) as f:
			config = yaml.load(f)
		templates = config['system']
		self._TEMPLATES = []
		self.templateChoices = []
		try:
			for t in templates.values():
				name = t['name']
				self._TEMPLATES.append(t)
				self.templateChoices.append(name)
			LOGGER.info(u'Load Config Completed.')
		except Exception, e:
			LOGGER.exception('Load Config error')
			wx.MessageBox(u'配置文件读取错误！查看错误详情请见%s' % CENTER_LOG_FILE, 'ERROR', wx.OK | wx.ICON_ERROR)

	def initUI(self):
		LOGGER.info(u'Init Application UI...')
		panel = wx.Panel(self)

		topSizer = wx.BoxSizer(wx.VERTICAL)
		
		#titleSizer = wx.BoxSizer(wx.HORIZONTAL)
		gridSizer = wx.FlexGridSizer(rows=3, cols=4, hgap=5, vgap=5)
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)

		folderSizer = wx.BoxSizer(wx.HORIZONTAL)
		filesSizer = wx.BoxSizer(wx.HORIZONTAL)
		dstSizer = wx.BoxSizer(wx.HORIZONTAL)

		msg = wx.StaticText(panel, wx.ID_ANY, u'')

		folderLabel = wx.StaticText(panel, label=u"程序选择")
		templateLabel = wx.StaticText(panel, label=u"数控系统")
		filesLabel = wx.StaticText(panel, label=u"程序文件")
		betweenLabel = wx.StaticText(panel, label=u"程序之间")
		nameLabel = wx.StaticText(panel, label=u"主程序名")
		toFolderLabel = wx.StaticText(panel, label=u"输出目录")


		self.folderRadio = wx.RadioButton(panel, label=u'目录') 
		self.filesRadio = wx.RadioButton(panel, label=u'文件') 
		self.filesRadio.SetValue(True)
		self.template = wx.Choice(panel, choices=self.templateChoices)
		self.Bind(wx.EVT_CHOICE, self.onChangeTemplate, self.template)

		#默认选中
		stringT = self.template.GetString(0)
		positionT = self.template.FindString(stringT)
		self.template.SetSelection(positionT)

		self.filesText = wx.TextCtrl(panel)
		filesBtn = wx.Button(panel, wx.ID_ANY, u'选择')
		self.Bind(wx.EVT_BUTTON, self.onSelectFolder, filesBtn)
		self.name = wx.TextCtrl(panel)
		self.toFolder = wx.TextCtrl(panel)
		dstBtn = wx.Button(panel, wx.ID_ANY, u'选择')
		self.Bind(wx.EVT_BUTTON, self.onSelectDst, dstBtn)
		self.between = wx.TextCtrl(panel)

		sb = wx.StaticBox(panel, label=u"文件清单")
		self.fileList = DragListStriped(panel,size = (400,250), style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
		self.fileList.InsertColumn(0, u"文件名称", width=150)
		self.fileList.InsertColumn(1, u"修改时间", width=200)
		self.fileList.InsertColumn(2, u"文件目录", width=100)
		self.fileList.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)

		listSizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

		okBtn = wx.Button(panel, wx.ID_ANY, u'生成')
		cancelBtn = wx.Button(panel, wx.ID_ANY, u'清除重选')

		#titleSizer.Add(msg, 0, wx.ALIGN_CENTER)

		folderSizer.Add(self.folderRadio, 0, wx.ALIGN_LEFT)
		folderSizer.Add(self.filesRadio, 0, wx.ALIGN_LEFT)
		filesSizer.Add(self.filesText, 0, wx.EXPAND)
		filesSizer.Add(filesBtn, 0, wx.ALIGN_LEFT)
		dstSizer.Add(self.toFolder, 0, wx.EXPAND)
		dstSizer.Add(dstBtn, 0, wx.ALIGN_LEFT)

		gridSizer.Add(folderLabel, 0, wx.ALIGN_RIGHT)
		gridSizer.Add(folderSizer, 0, wx.EXPAND)
		gridSizer.Add(templateLabel, 0, wx.ALIGN_RIGHT)
		gridSizer.Add(self.template, 0, wx.EXPAND)
		gridSizer.Add(filesLabel, 0, wx.ALIGN_RIGHT)
		gridSizer.Add(filesSizer, 0, wx.EXPAND)
		gridSizer.Add(nameLabel, 0, wx.ALIGN_RIGHT)
		gridSizer.Add(self.name, 0, wx.EXPAND)
		#gridSizer.Add((20,-1), proportion=1)
		#gridSizer.Add((20,-1), proportion=1)
		gridSizer.Add(toFolderLabel, 0, wx.ALIGN_RIGHT)
		gridSizer.Add(dstSizer, 0, wx.EXPAND)
		gridSizer.Add(betweenLabel, 0, wx.ALIGN_RIGHT)
		gridSizer.Add(self.between, 0, wx.EXPAND)
		#gridSizer.Add((20,-1), proportion=1)
		#gridSizer.Add((20,-1), proportion=1)

		listSizer.Add(self.fileList, 0, wx.EXPAND)

		btnSizer.Add(okBtn, 0, wx.ALL, 5)
		btnSizer.Add(cancelBtn, 0, wx.ALL, 5)
		self.Bind(wx.EVT_BUTTON, self.onOK, okBtn)
		self.Bind(wx.EVT_BUTTON, self.onCancel, cancelBtn)

		#topSizer.Add(titleSizer, 0, wx.CENTER)
		#topSizer.Add(wx.StaticLine(panel), 0, wx.ALL|wx.EXPAND, 5)
		gridSizer.AddGrowableCol(1)
		gridSizer.AddGrowableCol(3)
		topSizer.Add(gridSizer, 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(listSizer, 0, wx.ALL|wx.EXPAND, 5)
		#topSizer.Add(wx.StaticLine(panel), 0, wx.ALL|wx.EXPAND, 5)
		topSizer.Add(btnSizer, 0, wx.ALL|wx.CENTER, 5)

		# SetSizeHints(minW, minH, maxW, maxH)
		self.SetSizeHints(500, 520, 600, 550)
		 
		panel.SetSizer(topSizer)
		topSizer.Fit(self)

		menubar = wx.MenuBar(wx.MB_DOCKABLE)
		#------------create menus------------------
		file = wx.Menu()
		help = wx.Menu()
		
		file.Append(ID_REFRESH, u'&刷新配置\tCtrl+R', u'刷新配置')
		file.AppendSeparator()
		self.refresh_ckbox = file.AppendCheckItem(-1, u"读取默认值？")
		wx.EVT_MENU(self, -1, self.onLoadDefault)
		file.Check(self.refresh_ckbox.GetId(), True)
		file.AppendSeparator()
		file.Append(ID_EXIT, u'&退出\tCtrl+W', 'Exit Current window')

		help.Append(ID_HELP, u'&帮助', u'帮助')
		help.Append(ID_ABOUT, u'&关于', u'关于')
		self.Bind(wx.EVT_MENU, self.onExit, id=ID_EXIT)
		self.Bind(wx.EVT_MENU, self.onHelp, id=ID_HELP)
		self.Bind(wx.EVT_MENU, self.onAbout, id=ID_ABOUT)
		self.Bind(wx.EVT_MENU, self.onRefresh, id=ID_REFRESH)

		menubar.Append(file, u'&文件')
		menubar.Append(help, u'&帮助')

		self.SetMenuBar(menubar)

		self.statusbar = self.CreateStatusBar()
		self.statusbar.SetStatusText(u'Welcome !')
		self.InitValues()
		LOGGER.info(u'Init Application UI Completed.')

	def InitValues(self):
		selectedTpl = self.template.GetSelection()
		if selectedTpl < 0:
			self.template.SetSelection(0)
		self.onChangeTemplate()

	def OnMouseEvents(self,e):
		#print "Mouse event"
		if e.Entering():
			self.setMsg(u'Tip:键盘↑，↓ 切换列表选中; ← , → 进行移动; Delete 删除选中项；鼠标拖动可排序 。')
		elif e.Leaving():
			self.setMsg(u'')
		else:
			e.Skip()


	def onChangeTemplate(self, event=None):
		if self.loadDefault:
			cfg = self._TEMPLATES[self.template.GetSelection()]
			dft = cfg.get('default',{})
			self.between.SetValue(dft.get('between',''))
			self.name.SetValue(dft.get('name',''))

	def onLoadDefault(self, event):
		self.loadDefault = False if self.loadDefault == True else True
		if self.loadDefault:
			self.InitValues()
		else:
			#清空主程序名&程序之间
			selectedIndex = self.template.GetSelection()
			if selectedIndex < 0:
				return
			cfg = self._TEMPLATES[selectedIndex]
			dft = cfg.get('default',{})
			if self.between.GetValue() == dft.get('between','') and self.name.GetValue() == dft.get('name',''):
				self.between.SetValue('')
				self.name.SetValue('')

	def onSelectDst(self, event):
		"""
		选择目标目录
		"""
		selectedPath = None
		dialog = wx.DirDialog(None, u"请选择生成目录", style=wx.DD_NEW_DIR_BUTTON)
		if dialog.ShowModal() == wx.ID_OK:
			dir = dialog.GetPath()
			self.toFolder.SetValue(dir)
		dialog.Destroy()

	def onSelectFolder(self, event):
		"""
		选择文件
		"""
		selectedPath = None
		selectedIndex = self.template.GetSelection()
		sfx = None
		if selectedIndex >= 0:
			cfg = self._TEMPLATES[selectedIndex]
			sfx = cfg.get('limitSuffix',None)
			if sfx:
				sfx = sfx.lower()

		if sfx:
			upper_sfx = sfx.upper()
			wildcard = "File(*%s)|*%s;*%s" % (sfx, sfx, upper_sfx)
		else:
			wildcard = "All files(*.*)|*.*"
		isFolder = self.folderRadio.GetValue()
		if isFolder: 
			dialog = wx.DirDialog(None, u"请选择程序目录", style=wx.DD_DIR_MUST_EXIST)
			exist_dir = self.filesText.GetValue()
			if exist_dir:
				dialog.SetDirectory(exist_dir)
			if dialog.ShowModal() == wx.ID_OK:
				dir = dialog.GetPath()
				files = os.listdir(dir)
				self.validateFiles(files, dir)

		else:
			dialog = wx.FileDialog(None, u"请选择程序文件（可多选）", defaultDir=ROOT_DIR, wildcard=wildcard, style=wx.FD_MULTIPLE)
			exist_dir = self.filesText.GetValue()
			if exist_dir:
				dialog.SetDirectory(exist_dir)
			if dialog.ShowModal() == wx.ID_OK:
				dir = dialog.GetDirectory()
				files = dialog.GetFilenames()
				self.validateFiles(files, dir)

		dialog.Destroy()

	def validateFiles(self, files, dir):
		'''
		添加文件列表

		'''
		hasErr = False
		tExt = None
		for f in files:
			if not os.path.isfile(os.path.join(dir,f)):
				self.setMsg(u'不能添加目录:%s' % f, 'ERROR')
				hasErr = True
				break
			else:
				(fn, fext) = os.path.splitext(f)
				if tExt and fext.lower() != tExt:
					self.setMsg(u'选择的程序扩展名不统一, 请重新选择！', 'ERROR')
					hasErr = True
					break
				tExt = fext.lower()

		if not hasErr:
			#self.files = []
			self.src = dir
			self.filesText.SetValue(dir)
			#默认输出目录和源目录一致
			self.toFolder.SetValue(dir)

			for f in files:
				self.files.append((dir,f))

			self.refreshFileList()

			#self.setMsg(u'Tip: 拖动列表可排序, 按键盘Delete键可删除选中文件。')


	def onExit(self, event):
		self.Close(True)

	def onOK(self, event):
		cfg = self._TEMPLATES[self.template.GetSelection()]
		tpl = cfg['template']
		filename = self.name.GetValue()
		between = self.between.GetValue()
		outDir = self.toFolder.GetValue()
		dst = os.path.abspath(outDir)
		src = self.src
		needSuffix =  cfg.get('suffix', False)
		limitSfx = cfg.get('limitSuffix',None)
		if limitSfx:
			limitSfx = limitSfx.lower()

		if not filename:
			self.setMsg(u'请输入主程序名！','ERROR')
			return

		'''
		if not between:
			self.setMsg(u'请输入程序之间！','ERROR')
			return
		'''

		if not outDir:
			self.setMsg(u'请输入输出目录！','ERROR')
			return

		#取排序后的fileList
		count = self.fileList.GetItemCount()
		progs = []
		suffix = None
		for row in range(count):
			f = self.fileList.GetItem(itemId=row, col=0)
			src = self.fileList.GetItem(itemId=row, col=2)
			src = src.GetText()
			(fn, sfx) = os.path.splitext(f.GetText())
			progs.append((src, fn, sfx))
			if not suffix:
				suffix = sfx.lower()
			elif limitSfx and sfx.lower() != limitSfx:
				self.setMsg(u'选择的程序扩展名只能为%s, 请重新选择！' % limitSfx, 'ERROR')
				return
			elif suffix != sfx.lower():
				self.setMsg(u'选择的程序扩展名不统一, 请重新选择！', 'ERROR')
				return

		if not progs:
			self.setMsg(u'没有选择程序!', 'ERROR')
			return

		dstfile = None
		try:
			dstfile = generate(tpl, filename, suffix, needSuffix, between, src, dst, list(progs))
		except Exception, e:
			LOGGER.exception('Build template failed! %s' % str(e))
			self.setMsg(u'写入模板失败！%s ' % str(e), 'ERROR')
		else:
			LOGGER.info('Build template Completed!')
			self.setMsg(u'操作完成，成功写入模板！', 'SUCCESS')

		# open dstfile
		if dstfile:
			try:
				ret = subprocess.Popen('notepad.exe %s' % dstfile, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				#ret = os.system('notepad %s' % dstfile)
				LOGGER.info(u'Open dst file completed: %s' % dstfile)
			except Exception, e:
				LOGGER.error(u'Open dst file failed: %s' % dstfile)
				self.setMsg(u'打开文件目标文件失败!请手动打开程序文件：%s。' % dstfile, 'ERROR')


	def setMsg(self, msg, level='INFO'):
		if level == 'SUCCESS':
			self.statusbar.SetBackgroundColour(wx.GREEN)
		elif level == 'ERROR':
			self.statusbar.SetBackgroundColour(wx.RED)
		else:
			self.statusbar.SetBackgroundColour(wx.WHITE)

		self.statusbar.SetStatusText(msg)

	def onCancel(self, event):
		self.files = []
		self.fileList.DeleteAllItems()

	def onRefresh(self, event):
		self.loadConfig()
		self.template.SetItems(self.templateChoices)
		self.InitValues()

	def onAbout(self, event):
		info = wx.AboutDialogInfo()
		info.Name = u'NCString'
		info.Version = "v0.1.0 beta"
		info.Copyright = "(C) 2013"
		'''
		info.Description = wordwrap(
			u"本软件旨为实际数控编程提供便利，如在使用中有任何问题，请联系我。",
			350, wx.ClientDC(self))
		info.WebSite = ("http://angellin0.iteye.com/", "Alvin Yao")
		'''
		info.Developers = ["Alvin Yao"]
		wx.AboutBox(info)

	def onHelp(self, event):
		try:
			ret = subprocess.Popen('explorer.exe %s' % os.path.join(ROOT_DIR, 'help/readme.html'), shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			#ret = os.system('explorer %s' % os.path.join(ROOT_DIR, 'readme.html'))
			LOGGER.info(u'打开文件readme.html: %s' % os.path.join(ROOT_DIR, 'help/readme.html'))
		except Exception, e:
			LOGGER.error(u'打开文件readme.html失败%s' % str(e))
			self.setMsg(u'请打开程序主目录readme.html查看帮助信息。', 'ERROR')

	def refreshFileList(self):
		'''
		刷新文件列表
		'''
		#self.files = sorted(self.files, reverse=False)
		self.fileList.DeleteAllItems()
		for index in range(len(self.files)):
			i = self.fileList.InsertStringItem(index,self.files[index][1]) 
			self.fileList.SetStringItem(i, 1, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(os.path.getmtime(os.path.join(self.files[index][0], self.files[index][1])))))
			self.fileList.SetStringItem(i, 2, self.files[index][0]) 

def generate(template, filename, fileSuffix, needSuffix, between, src, dst, files):
	"""
	模板生成主函数
	"""
	tpl = Template(filename=os.path.join(ROOT_DIR, template), input_encoding='utf-8', 
		output_encoding='utf-8', default_filters=['decode.utf8'], 
		encoding_errors='replace' )

	callSuffix = fileSuffix
	if not needSuffix:
		callSuffix = ''

	progs = []
	for item in files:
		if needSuffix:
			progs.append({'name':item[1], 'suffix': item[2]})
		else:
			progs.append({'name':item[1], 'suffix': ''})
	
	renderText = tpl.render(filename=filename, between=between, progs=progs)

	if not os.path.isdir(dst):
		try:
			os.makedirs(dst)
		except OSError as exc:  # Python >2.5
			if exc.errno == errno.EEXIST:
				pass
			else: raise

	dstfile = os.path.join(dst, u'%s%s' %(filename, fileSuffix))
	with open(dstfile,'w') as f:
		f.write(renderText)

	# Copy files
	#if src != dst:
	for item in files:
		filename = u'%s%s' %(item[1], item[2])
		from_path = os.path.join(item[0], filename)
		dst_path = os.path.join(dst,filename)
		if from_path != dst_path:
			shutil.copyfile(from_path, dst_path)

	return dstfile
	

if __name__ == '__main__':
	app = wx.App()
	NCString(None, title=u'NCString')
	app.MainLoop()
