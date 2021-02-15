# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Dec 18 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

from .TreePanel import TreePanel
from .RAMTreePanel import RAMTreePanel
from .ConsolePanel import ConsolePanel
from .BaseFrame import BaseFrame
from .LoggerParamPanel import LoggerParamPanel
from .LoggerGaugePanel import LoggerGaugePanel
import wx
import wx.xrc
import wx.propgrid as pg
import wx.aui

###########################################################################
## Class PrefsDialog
###########################################################################

class PrefsDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Preferences", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.CAPTION|wx.RESIZE_BORDER|wx.STAY_ON_TOP )

        self.SetSizeHints( wx.Size( 400,400 ), wx.DefaultSize )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._PGM = pg.PropertyGridManager(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.propgrid.PGMAN_DEFAULT_STYLE|wx.propgrid.PG_BOLD_MODIFIED|wx.propgrid.PG_DESCRIPTION|wx.propgrid.PG_NO_INTERNAL_BORDER|wx.propgrid.PG_SPLITTER_AUTO_CENTER|wx.propgrid.PG_TOOLTIPS)
        self._PGM.SetExtraStyle( wx.propgrid.PG_EX_MODE_BUTTONS )

        self._prop_page = self._PGM.AddPage( u"Editor Preferences", wx.NullBitmap );
        _sizer.Add( self._PGM, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 0 )


        _sizer.Add( ( 0, 0 ), wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )

        _button_sizer = wx.StdDialogButtonSizer()
        self._button_sizerSave = wx.Button( self, wx.ID_SAVE )
        _button_sizer.AddButton( self._button_sizerSave )
        self._button_sizerCancel = wx.Button( self, wx.ID_CANCEL )
        _button_sizer.AddButton( self._button_sizerCancel )
        _button_sizer.Realize();

        _sizer.Add( _button_sizer, wx.GBPosition( 2, 0 ), wx.GBSpan( 1, 1 ), wx.ALIGN_CENTER_HORIZONTAL, 0 )


        _sizer.AddGrowableCol( 0 )
        _sizer.AddGrowableRow( 0 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_INIT_DIALOG, self.OnInitialize )
        self._PGM.Bind( pg.EVT_PG_CHANGING, self.OnEdit )
        self._button_sizerCancel.Bind( wx.EVT_BUTTON, self.OnCancel )
        self._button_sizerSave.Bind( wx.EVT_BUTTON, self.OnCommit )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnInitialize( self, event ):
        event.Skip()

    def OnEdit( self, event ):
        event.Skip()

    def OnCancel( self, event ):
        event.Skip()

    def OnCommit( self, event ):
        event.Skip()


###########################################################################
## Class bEditorFrame
###########################################################################

class bEditorFrame ( BaseFrame ):

    def __init__( self, parent ):
        BaseFrame.__init__ ( self, parent, id = wx.ID_ANY, title = u"PyRRhic Editor", pos = wx.DefaultPosition, size = wx.Size( 1000,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        self.m_mgr = wx.aui.AuiManager()
        self.m_mgr.SetManagedWindow( self )
        self.m_mgr.SetFlags(wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE|wx.aui.AUI_MGR_ALLOW_FLOATING|wx.aui.AUI_MGR_LIVE_RESIZE|wx.aui.AUI_MGR_TRANSPARENT_HINT)

        self._menubar = wx.MenuBar( 0 )
        self._m_file = wx.Menu()
        self._mi_open = wx.MenuItem( self._m_file, wx.ID_ANY, u"Open ROM"+ u"\t" + u"CTRL+O", u"Open a binary ROM file", wx.ITEM_NORMAL )
        self._mi_open.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_FILE_OPEN, wx.ART_MENU ) )
        self._m_file.Append( self._mi_open )

        self._mi_save = wx.MenuItem( self._m_file, wx.ID_ANY, u"Save ROM"+ u"\t" + u"CTRL+S", u"Save edited ROM file(s)", wx.ITEM_NORMAL )
        self._mi_save.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_FILE_SAVE, wx.ART_MENU ) )
        self._m_file.Append( self._mi_save )

        self._mi_save_as = wx.MenuItem( self._m_file, wx.ID_ANY, u"Save ROM As"+ u"\t" + u"CTRL+SHIFT+S", u"Save edited ROM file(s) as", wx.ITEM_NORMAL )
        self._mi_save_as.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_FILE_SAVE_AS, wx.ART_MENU ) )
        self._m_file.Append( self._mi_save_as )

        self._mi_file_prefs = wx.MenuItem( self._m_file, wx.ID_ANY, u"Preferences"+ u"\t" + u"CTRL+P", u"Open Preferences", wx.ITEM_NORMAL )
        self._mi_file_prefs.SetBitmap( wx.NullBitmap )
        self._m_file.Append( self._mi_file_prefs )

        self._m_file.AppendSeparator()

        self._mi_exit = wx.MenuItem( self._m_file, wx.ID_ANY, u"Exit"+ u"\t" + u"ALT+F4", u"Exit", wx.ITEM_NORMAL )
        self._mi_exit.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_QUIT, wx.ART_MENU ) )
        self._m_file.Append( self._mi_exit )

        self._menubar.Append( self._m_file, u"File" )

        self._m_view = wx.Menu()
        self._mi_view_romdata = wx.MenuItem( self._m_view, wx.ID_ANY, u"ROM Data", u"Toggle Loaded ROMs Pane", wx.ITEM_CHECK )
        self._mi_view_romdata.SetBitmap( wx.NullBitmap )
        self._m_view.Append( self._mi_view_romdata )
        self._mi_view_romdata.Check( True )

        self._mi_view_console = wx.MenuItem( self._m_view, wx.ID_ANY, u"Console", u"Toggle Console Pane", wx.ITEM_CHECK )
        self._mi_view_console.SetBitmap( wx.NullBitmap )
        self._m_view.Append( self._mi_view_console )
        self._mi_view_console.Check( True )

        self._mi_view_livetune = wx.MenuItem( self._m_view, wx.ID_ANY, u"Live Tuning", u"Toggle Live Tuning Pane", wx.ITEM_CHECK )
        self._mi_view_livetune.SetBitmap( wx.NullBitmap )
        self._m_view.Append( self._mi_view_livetune )
        self._mi_view_livetune.Enable( False )

        self._menubar.Append( self._m_view, u"View" )

        self.SetMenuBar( self._menubar )

        self._toolbar = wx.aui.AuiToolBar( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.aui.AUI_TB_HORZ_LAYOUT )
        self._tb_open = self._toolbar.AddTool( wx.ID_ANY, u"Open ROM", wx.ArtProvider.GetBitmap( wx.ART_FILE_OPEN, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Open ROM", u"Open ROM", None )

        self._tb_save = self._toolbar.AddTool( wx.ID_ANY, u"Save ROM", wx.ArtProvider.GetBitmap( wx.ART_FILE_SAVE, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Save ROM", u"Save ROM", None )

        self._tb_save_as = self._toolbar.AddTool( wx.ID_ANY, u"Save ROM As", wx.ArtProvider.GetBitmap( wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Save ROM As", u"Save ROM As", None )

        self._toolbar.Realize()
        self.m_mgr.AddPane( self._toolbar, wx.aui.AuiPaneInfo().Top().CaptionVisible( False ).CloseButton( False ).PaneBorder( False ).Movable( False ).Dock().Resizable().FloatingSize( wx.Size( -1,-1 ) ).DockFixed( True ).BottomDockable( False ).LeftDockable( False ).RightDockable( False ).Floatable( False ).Layer( 10 ) )

        self._status_bar = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )
        self._tree_panel = TreePanel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_mgr.AddPane( self._tree_panel, wx.aui.AuiPaneInfo() .Name( u"RomDataPane" ).Left() .Caption( u"ROM Data" ).PaneBorder( False ).Dock().Resizable().FloatingSize( wx.DefaultSize ).BottomDockable( False ).TopDockable( False ).Row( 1 ).MinSize( wx.Size( 400,-1 ) ) )

        self._livetune_panel = RAMTreePanel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_mgr.AddPane( self._livetune_panel, wx.aui.AuiPaneInfo() .Name( u"RAMTablePane" ).Left() .Caption( u"RAM Tables" ).PaneBorder( False ).Hide().Dock().Resizable().FloatingSize( wx.DefaultSize ).BottomDockable( False ).TopDockable( False ).Row( 1 ).MinSize( wx.Size( 400,-1 ) ) )

        self._console_panel = ConsolePanel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_mgr.AddPane( self._console_panel, wx.aui.AuiPaneInfo() .Name( u"ConsolePane" ).Center() .Caption( u"Console" ).PaneBorder( False ).Dock().Resizable().FloatingSize( wx.Size( -1,-1 ) ).Row( 1 ).Position( 0 ).MinSize( wx.Size( 600,-1 ) ) )


        self.m_mgr.Update()
        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnTogglePane )
        self.Bind( wx.EVT_CLOSE, self.OnClose )
        self.Bind( wx.EVT_MENU, self.OnOpenRom, id = self._mi_open.GetId() )
        self.Bind( wx.EVT_MENU, self.OnSaveRom, id = self._mi_save.GetId() )
        self.Bind( wx.EVT_MENU, self.OnSaveRomAs, id = self._mi_save_as.GetId() )
        self.Bind( wx.EVT_MENU, self.OnPreferences, id = self._mi_file_prefs.GetId() )
        self.Bind( wx.EVT_MENU, self.OnClose, id = self._mi_exit.GetId() )
        self.Bind( wx.EVT_MENU, self.OnTogglePane, id = self._mi_view_romdata.GetId() )
        self.Bind( wx.EVT_MENU, self.OnTogglePane, id = self._mi_view_console.GetId() )
        self.Bind( wx.EVT_MENU, self.OnTogglePane, id = self._mi_view_livetune.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnOpenRom, id = self._tb_open.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnSaveRom, id = self._tb_save.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnSaveRomAs, id = self._tb_save_as.GetId() )

    def __del__( self ):
        self.m_mgr.UnInit()



    # Virtual event handlers, overide them in your derived class
    def OnTogglePane( self, event ):
        event.Skip()

    def OnClose( self, event ):
        event.Skip()

    def OnOpenRom( self, event ):
        event.Skip()

    def OnSaveRom( self, event ):
        event.Skip()

    def OnSaveRomAs( self, event ):
        event.Skip()

    def OnPreferences( self, event ):
        event.Skip()









###########################################################################
## Class bLoggerFrame
###########################################################################

class bLoggerFrame ( BaseFrame ):

    def __init__( self, parent ):
        BaseFrame.__init__ ( self, parent, id = wx.ID_ANY, title = u"PyRRhic Logger", pos = wx.DefaultPosition, size = wx.Size( 800,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        self.m_mgr = wx.aui.AuiManager()
        self.m_mgr.SetManagedWindow( self )
        self.m_mgr.SetFlags(wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE)

        self._menubar = wx.MenuBar( 0 )
        self.SetMenuBar( self._menubar )

        self._toolbar = wx.aui.AuiToolBar( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.aui.AUI_TB_HORZ_LAYOUT )
        self._refresh_but = self._toolbar.AddTool( wx.ID_ANY, u"tool", wx.ArtProvider.GetBitmap( wx.ART_FIND, wx.ART_BUTTON ), wx.NullBitmap, wx.ITEM_NORMAL, u"Refresh Device List", u"Refresh Device List", None )

        _iface_choiceChoices = [ u"Interface Selection" ]
        self._iface_choice = wx.Choice( self._toolbar, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, _iface_choiceChoices, 0 )
        self._iface_choice.SetSelection( 0 )
        self._toolbar.AddControl( self._iface_choice )
        _protocol_choiceChoices = [ u"Protocol Selection" ]
        self._protocol_choice = wx.Choice( self._toolbar, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, _protocol_choiceChoices, 0 )
        self._protocol_choice.SetSelection( 0 )
        self._toolbar.AddControl( self._protocol_choice )
        self._connect_but = wx.Button( self._toolbar, wx.ID_ANY, u"Connect", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._connect_but.Enable( False )

        self._toolbar.AddControl( self._connect_but )
        self._toolbar.Realize()
        self.m_mgr.AddPane( self._toolbar, wx.aui.AuiPaneInfo().Bottom().CaptionVisible( False ).CloseButton( False ).PinButton( True ).Movable( False ).Dock().Resizable().FloatingSize( wx.DefaultSize ).LeftDockable( False ).RightDockable( False ).Layer( 10 ) )

        self._statusbar = self.CreateStatusBar( 3, wx.STB_DEFAULT_STYLE, wx.ID_ANY )
        self._param_panel = LoggerParamPanel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_mgr.AddPane( self._param_panel, wx.aui.AuiPaneInfo() .Left() .Caption( u"Parameters" ).Dock().Resizable().FloatingSize( wx.DefaultSize ).BottomDockable( False ).TopDockable( False ).MinSize( wx.Size( 200,-1 ) ).Layer( 10 ) )

        self._gauge_panel = LoggerGaugePanel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_mgr.AddPane( self._gauge_panel, wx.aui.AuiPaneInfo() .Center() .Caption( u"Gauges" ).CloseButton( False ).Dock().Resizable().FloatingSize( wx.DefaultSize ).BottomDockable( False ).TopDockable( False ).Floatable( False ).DefaultPane() )


        self.m_mgr.Update()
        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_IDLE, self.OnIdle )
        self.Bind( wx.EVT_TOOL, self.OnRefreshInterfaces, id = self._refresh_but.GetId() )
        self._iface_choice.Bind( wx.EVT_CHOICE, self.OnSelectInterface )
        self._protocol_choice.Bind( wx.EVT_CHOICE, self.OnSelectProtocol )
        self._connect_but.Bind( wx.EVT_BUTTON, self.OnConnectButton )

    def __del__( self ):
        self.m_mgr.UnInit()



    # Virtual event handlers, overide them in your derived class
    def OnIdle( self, event ):
        event.Skip()

    def OnRefreshInterfaces( self, event ):
        event.Skip()

    def OnSelectInterface( self, event ):
        event.Skip()

    def OnSelectProtocol( self, event ):
        event.Skip()

    def OnConnectButton( self, event ):
        event.Skip()


